import pandas as pd
import sys
from pathlib import Path
import re 
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from models.model_registry import ModelRegistry
import joblib
import pickle
import os
from typing import Dict, Any, Optional, List

class SimpleAutoML:
    def __init__(self, target_col='purchase_price', test_split=0.2, cv_folds=3):
        self.target_col = target_col
        self.test_split = test_split
        self.cv_folds = cv_folds
        
        # Components that will be fitted
        self.scaler = StandardScaler()
        # Removed: self.label_encoders = {}  # Not needed for pre-encoded data
        self.feature_selector = None
        self.best_model = None
        self.model_registry = ModelRegistry()
        
        # Results storage
        self.results = {}
        
        # Store data preprocessing info for later use
        self.feature_columns = None
        self.sanitized_feature_names = None
        self.original_feature_names = None
        
    def save_model(self, filepath: str, include_results: bool = True):
        """Save the trained AutoML model and preprocessing components to disk."""
        if self.best_model is None:
            raise ValueError("No model has been trained yet. Call run_automl() first.")
        
        # Create directory if it doesn't exist
        base_dir = os.path.dirname(filepath) if os.path.dirname(filepath) else '.'
        os.makedirs(base_dir, exist_ok=True)
        
        # Create model package with metadata
        model_package = {
            'model': self.best_model,
            'feature_selector': self.feature_selector,
            'scaler': self.scaler,
            'target_col': self.target_col,
            'feature_columns': self.feature_columns,
            'model_metadata': {
                'best_model_name': self.results.get('best_model', 'unknown'),
                'save_timestamp': pd.Timestamp.now().isoformat()
            }
        }
        
        if include_results:
            model_package['results'] = self.results
        
        # Save main package
        main_path = f"{filepath}.pkl"
        joblib.dump(model_package, main_path)
        print(f"Model package saved to: {main_path}")
        
        # Let the model save its own weights if it wants to
        if hasattr(self.best_model, 'save_model'):
            try:
                weights_path = self.best_model.save_model(filepath)
                if weights_path:
                    print(f"Model weights saved to: {weights_path}")
            except Exception as e:
                print(f"Warning: Could not save model weights: {e}")
        
        return main_path

    def _detect_model_type(self, model):
        """
        Detect the type of model for proper saving/loading.
        
        Args:
            model: The trained model object
            
        Returns:
            str: Model type identifier
        """
        model_class = type(model).__name__
        model_module = type(model).__module__
        
        # Check for specific model types
        if 'sklearn' in model_module or 'linear_model' in model_module:
            return 'sklearn'
        elif 'lightgbm' in model_module or model_class == 'LGBMRegressor':
            return 'lightgbm'
        elif 'xgboost' in model_module or model_class == 'XGBRegressor':
            return 'xgboost'
        else:
            # Check for common deep learning frameworks by trying imports
            try:
                import tensorflow as tf
                if isinstance(model, tf.keras.Model):
                    return 'tensorflow'
            except ImportError:
                pass
            
            try:
                import torch
                if isinstance(model, torch.nn.Module):
                    return 'pytorch'
            except ImportError:
                pass
            
            # Default to sklearn-compatible
            return 'sklearn'

    def run_automl(self, df: pd.DataFrame, 
               feature_selection_fn=None,
               hypertuning_fn=None,
               models_to_run: Optional[List[str]] = None,
               n_splits=5,
               test_split=0.2,
               verbose=1, param_amount='small',
               loss_fn=None) -> Dict[str, Any]:

        print("Starting AutoML Pipeline - Training ALL available models...")
        
        # Step 1: Split data (without scaling - we'll scale within CV)
        X_train, X_test, y_train, y_test = self._prepare_data_splits_no_scaling(df, test_split)
        
        # Create CV splitter for feature selection and hypertuning
        cv = TimeSeriesSplit(n_splits=n_splits)
        
        # Step 2: Train ALL available models (with individual feature selection)
        model_results = {}
        all_model_names = models_to_run if models_to_run is not None else self.model_registry.list_models()
        print(f"Training {len(all_model_names)} models: {all_model_names}")
        
        for model_name in all_model_names:
            print(f"\nTraining {model_name}...")
            try:
                model_config = self.model_registry.get_model_config(model_name)
                
                # Create copies of data for this model
                X_train_model = X_train.copy()
                X_test_model = X_test.copy()
                
                # Step 2a: Feature selection for THIS specific model (if provided)
                feature_selector = None
                if feature_selection_fn is not None:
                    print(f"  Running feature selection for {model_name}...")
                    
                    # Create a quick model instance for feature selection
                    selector_model = model_config.get_model(loss_fn=loss_fn)
                    
                    # Create feature selector with CV parameter
                    feature_selector = feature_selection_fn(
                        estimator=selector_model,
                         loss_fn=loss_fn,
                        cv=cv,  # Pass CV splitter
                        verbose=verbose,
                    )

                    # Fit on training data, transform both sets
                    X_train_model = feature_selector.fit_transform(X_train_model, y_train)
                    X_test_model = feature_selector.transform(X_test_model)
                    
                    print(f"  Features after selection for {model_name}: {X_train_model.shape[1]}")
                
                # Step 2b: Hyperparameter tuning for THIS model (if provided)
                if hypertuning_fn is not None:
                    print(f"  Running hyperparameter tuning for {model_name}...")
                    
                    # Get parameter grid
                   
                    param_grid = model_config.get_param_grid(param_amount)
                    base_model = model_config.get_model(loss_fn=loss_fn)
                    # Create and fit tuner with CV parameter
                    tuner = hypertuning_fn(
                        estimator=base_model,
                        loss_fn=loss_fn,
                        param_grid=param_grid,
                        cv=cv,  # Pass same CV splitter
                        n_jobs=-1,
                        verbose=verbose
                    )

                    tuner.fit(X_train_model, y_train)  # Uses feature-selected data
                    best_params = tuner.best_params_
                    cv_score = tuner.best_score_
                    
                    print(f"  Best params for {model_name}: {best_params}")
                else:
                    # Use default parameters
                    best_params = {}
                    cv_score = None
                    print(f"  Using default parameters for {model_name}")
                
                # Step 2c: Train final model with proper scaling
                result = self._train_and_evaluate_with_scaling(
                    model_config, best_params, X_train_model, y_train, X_test_model, y_test, loss_fn, cv_score
                )
                
                # Store feature selector info in results
                result['feature_selector'] = feature_selector
                result['n_features_selected'] = X_train_model.shape[1]
                result['original_features'] = X_train.shape[1]
                
                model_results[model_name] = result
                print(f"✓ {model_name} - Test {loss_fn.name}: {result['metrics']['test_loss']:.2f} (Features: {X_train_model.shape[1]})")

            except Exception as e:
                print(f"✗ {model_name} failed: {str(e)}")
                model_results[model_name] = {'error': str(e)}
        
        # Step 3: Find best model and store results
        best_model_name, best_result = self._get_best_model(model_results , loss_fn)
        self.best_model = best_result['model']
        self.feature_selector = best_result.get('feature_selector')
        
        self.results = {
            'models': model_results,
            'best_model': best_model_name,
            'data_info': {
                'train_size': len(X_train),
                'test_size': len(X_test),
                'original_features': X_train.shape[1],
                'feature_selection_used': feature_selection_fn is not None,
                'hypertuning_used': hypertuning_fn is not None,
                'models_trained': len(all_model_names)
            }
        }

        self._print_results(loss_fn)
        return self.results

    def _prepare_data_splits_no_scaling(self, df, test_split):
        """Split data without scaling - scaling happens within CV"""
        # Get features and target
        feature_cols = [col for col in df.columns if col not in ['date', self.target_col]]
        X = df[feature_cols].copy()
        y = df[self.target_col].copy()

        # --- NEW: Sanitize column names ---
        self.original_feature_names = X.columns.tolist()
        sanitized_cols = {col: re.sub(r'[^a-zA-Z0-9_]', '_', col) for col in X.columns}
        X = X.rename(columns=sanitized_cols)
        self.sanitized_feature_names = X.columns.tolist()
        self.feature_columns = self.sanitized_feature_names  # Store for saving
        # --- End of new code ---
        
        # Simple time series split for final train/test
        split_point = int(len(df) * (1 - test_split))
        
        X_train = X.iloc[:split_point].copy()
        X_test = X.iloc[split_point:].copy()
        y_train = y.iloc[:split_point].copy()
        y_test = y.iloc[split_point:].copy()
        
        print(f"Data split - Train: {len(X_train)}, Test: {len(X_test)}")
        return X_train, X_test, y_train, y_test

    def _train_and_evaluate_with_scaling(self, model_config, params, X_train, y_train, X_test, y_test, loss_fn, cv_score=None):
        """Train final model with proper scaling"""
        from helper.helper import helper  # Import helper
        
        # Scale final train/test data
        data_scaler = helper()
        X_train_scaled, X_test_scaled = data_scaler.scale(X_train, X_test)
        
        # Train model on scaled data
        model, y_pred = model_config.train_and_predict(X_train_scaled, y_train, X_test_scaled, loss_fn=loss_fn, **params)
        
        # Calculate metrics using consistent naming
        y_train_pred = model.predict(X_train_scaled)
        metrics = {
            'train_loss': loss_fn(y_train, y_train_pred),  # Simplified naming
            'test_loss': loss_fn(y_test, y_pred)           # Simplified naming
        }

        result = {
            'model': model,
            'params': params,
            'metrics': metrics,
            'model_name': model_config.get_model_name()
        }
        
        if cv_score is not None:
            result['cv_score'] = cv_score
            
        return result


    # Add this method to automl.py:
    def _get_best_model(self, model_results, loss_fn):
        """Get best model based on test metric"""
        valid_results = {name: result for name, result in model_results.items() 
                        if 'error' not in result and 'metrics' in result}
        
        if not valid_results:
            raise ValueError("No valid models found")
        
        # Use consistent metric key
        metric_key = 'test_loss'
        
        # Find model with lowest test error (since lower is better for mae/rmse)
        best_name = min(valid_results.keys(), 
                       key=lambda x: valid_results[x]['metrics'].get(metric_key, float('inf')))

        return best_name, valid_results[best_name]
    
    def _print_results(self, loss_fn):
        """Print results summary"""
        print("\n" + "="*60)
        print("AUTOML RESULTS")
        print("="*60)
        
        for model_name, result in self.results['models'].items():
            if 'error' in result:
                print(f"{model_name}: FAILED - {result['error']}")
            else:
                metrics = result['metrics']
                print(f"{model_name}: Test {loss_fn.name}: {metrics['test_loss']:,.2f}")

        print(f"\nBest Model: {self.results['best_model']}")
        best_metrics = self.results['models'][self.results['best_model']]['metrics']
        print(f"Best Test {loss_fn.name}: {best_metrics['test_loss']:,.2f}")