import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from feature_selection.backwards import BackwardFeatureSelector
from hyper_tuning.grid_search import GridSearchTuner
from models.model_registry import ModelRegistry
import joblib
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
    
    def run_automl(self, df: pd.DataFrame, 
               feature_selection_fn=None,
               hypertuning_fn=None,
               n_splits=5,
               test_split=0.2,
               verbose=1, param_amount='small') -> Dict[str, Any]:

        print("Starting AutoML Pipeline - Training ALL available models...")
        
        # Step 1: Split data (without scaling - we'll scale within CV)
        X_train, X_test, y_train, y_test = self._prepare_data_splits_no_scaling(df, test_split)
        
        # Create CV splitter for feature selection and hypertuning
        cv = TimeSeriesSplit(n_splits=n_splits)
        
        # Step 2: Train ALL available models (with individual feature selection)
        model_results = {}
        all_model_names = self.model_registry.list_models()
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
                    selector_model = model_config.get_model()
                    
                    # Create feature selector with CV parameter
                    feature_selector = feature_selection_fn(
                        estimator=selector_model,
                        cv=cv,  # Pass CV splitter
                        scoring='neg_mean_squared_error',
                        verbose=verbose
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
                    base_model = model_config.get_model()
                    # Create and fit tuner with CV parameter
                    tuner = hypertuning_fn(
                        estimator=base_model,
                        param_grid=param_grid,
                        cv=cv,  # Pass same CV splitter
                        scoring='neg_mean_squared_error',
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
                    model_config, best_params, X_train_model, y_train, X_test_model, y_test, cv_score
                )
                
                # Store feature selector info in results
                result['feature_selector'] = feature_selector
                result['n_features_selected'] = X_train_model.shape[1]
                result['original_features'] = X_train.shape[1]
                
                model_results[model_name] = result
                print(f"✓ {model_name} - Test RMSE: {result['metrics']['test_rmse']:.2f} (Features: {X_train_model.shape[1]})")
                
            except Exception as e:
                print(f"✗ {model_name} failed: {str(e)}")
                model_results[model_name] = {'error': str(e)}
        
        # Step 3: Find best model and store results
        best_model_name, best_result = self._get_best_model(model_results)
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
        
        self._print_results()
        return self.results

    def _prepare_data_splits_no_scaling(self, df, test_split):
        """Split data without scaling - scaling happens within CV"""
        # Get features and target
        feature_cols = [col for col in df.columns if col not in ['date', self.target_col]]
        X = df[feature_cols].copy()
        y = df[self.target_col].copy()
        
        # Simple time series split for final train/test
        split_point = int(len(df) * (1 - test_split))
        
        X_train = X.iloc[:split_point].copy()
        X_test = X.iloc[split_point:].copy()
        y_train = y.iloc[:split_point].copy()
        y_test = y.iloc[split_point:].copy()
        
        print(f"Data split - Train: {len(X_train)}, Test: {len(X_test)}")
        return X_train, X_test, y_train, y_test

    def _train_and_evaluate_with_scaling(self, model_config, params, X_train, y_train, X_test, y_test, cv_score=None):
        """Train final model with proper scaling"""
        from helper.helper import helper  # Import helper
        
        # Scale final train/test data
        data_scaler = helper()
        X_train_scaled, X_test_scaled = data_scaler.scale(X_train, X_test)
        
        # Store the fitted scaler
       
        
        # Train model on scaled data
        model, y_pred = model_config.train_and_predict(X_train_scaled, y_train, X_test_scaled, **params)
        
        # Calculate metrics
        y_train_pred = model.predict(X_train_scaled)
        metrics = {
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            'train_r2': r2_score(y_train, y_train_pred),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'test_r2': r2_score(y_test, y_pred)
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
    def _get_best_model(self, model_results):
        """Get best model based on test RMSE"""
        valid_results = {name: result for name, result in model_results.items() 
                        if 'error' not in result}
        
        if not valid_results:
            raise ValueError("No valid models found")
        
        best_name = min(valid_results.keys(), 
                    key=lambda x: valid_results[x]['metrics']['test_rmse'])
        
        return best_name, valid_results[best_name]
    def _print_results(self):
        """Print results summary"""
        print("\n" + "="*60)
        print("AUTOML RESULTS")
        print("="*60)
        
        for model_name, result in self.results['models'].items():
            if 'error' in result:
                print(f"{model_name}: FAILED - {result['error']}")
            else:
                metrics = result['metrics']
                print(f"{model_name}: Test RMSE: {metrics['test_rmse']:,.2f}, R²: {metrics['test_r2']:.4f}")
        
        print(f"\nBest Model: {self.results['best_model']}")
        best_metrics = self.results['models'][self.results['best_model']]['metrics']
        print(f"Best Test RMSE: {best_metrics['test_rmse']:,.2f}")
        print(f"Best Test R²: {best_metrics['test_r2']:.4f}")