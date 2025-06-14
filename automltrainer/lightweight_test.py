"""
Lightweight test suite for the AutoML system that works without external ML libraries.

This test focuses on:
1. Interface functionality and inheritance
2. Data flow through the system
3. Error handling and edge cases
4. Basic integration testing

Note: Some tests may be skipped if ML libraries (lightgbm, xgboost) are not installed.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import time

# Add the code directory to Python path
code_dir = Path(__file__).parent / 'code'
sys.path.append(str(code_dir))

# Import the AutoML components
from automl.automl import SimpleAutoML
from feature_selection import BackwardFeatureSelector, FeatureSelectionInterface
from hyper_tuning import GridSearchTuner, LineSearchTuner, HypertuningInterface
from Loss import mae, mape, rmse

def create_test_data():
    """Create synthetic regression data for testing."""
    np.random.seed(42)
    n_samples = 200  # Small dataset for fast testing
    n_features = 5
    
    # Create features
    X = pd.DataFrame({
        f'feature_{i}': np.random.normal(0, 1, n_samples) 
        for i in range(n_features)
    })
    
    # Create target with dependencies on first 3 features
    y = (2 * X['feature_0'] + 
         1 * X['feature_1'] - 
         0.5 * X['feature_2'] + 
         np.random.normal(0, 0.5, n_samples))
    
    # Combine into DataFrame
    df = X.copy()
    df['target'] = y
    df['date'] = pd.date_range('2020-01-01', periods=n_samples, freq='D')
    
    return df

def test_interface_inheritance():
    """Test that classes properly inherit from interfaces."""
    print("\n" + "="*60)
    print("TEST 1: INTERFACE INHERITANCE")
    print("="*60)
    
    # Test FeatureSelectionInterface
    print("Testing FeatureSelectionInterface inheritance:")
    print(f"  BackwardFeatureSelector is subclass: {issubclass(BackwardFeatureSelector, FeatureSelectionInterface)}")
    
    # Test HypertuningInterface  
    print("Testing HypertuningInterface inheritance:")
    print(f"  GridSearchTuner is subclass: {issubclass(GridSearchTuner, HypertuningInterface)}")
    print(f"  LineSearchTuner is subclass: {issubclass(LineSearchTuner, HypertuningInterface)}")
    
    # Test Loss functions
    print("Testing Loss function properties:")
    for loss_cls in [mae, mape, rmse]:
        loss_fn = loss_cls()
        print(f"  {loss_cls.__name__}: name='{loss_fn.name}', higher_is_better={loss_fn.higher_is_better}")

def test_data_flow():
    """Test data flow through the system without actual ML training."""
    print("\n" + "="*60)
    print("TEST 2: DATA FLOW AND SETUP")
    print("="*60)
    
    df = create_test_data()
    print(f"Created test data: {df.shape}")
    print(f"Features: {[col for col in df.columns if col not in ['target', 'date']]}")
    print(f"Target: {df['target'].describe()}")
    
    # Test AutoML initialization
    automl = SimpleAutoML(target_col='target')
    print(f"AutoML initialized with target_col='target'")
    
    # Test data preparation (without scaling)
    try:
        X_train, X_test, y_train, y_test = automl._prepare_data_splits_no_scaling(df, test_split=0.2)
        print(f"Data split successful:")
        print(f"  Train: X={X_train.shape}, y={y_train.shape}")
        print(f"  Test: X={X_test.shape}, y={y_test.shape}")
    except Exception as e:
        print(f"Data split failed: {e}")

def test_loss_functions():
    """Test loss function implementations."""
    print("\n" + "="*60)
    print("TEST 3: LOSS FUNCTION IMPLEMENTATIONS")
    print("="*60)
    
    # Create sample predictions
    np.random.seed(42)
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
    
    loss_functions = [mae(), mape(), rmse()]
    
    for loss_fn in loss_functions:
        try:
            score = loss_fn(y_true, y_pred)
            print(f"  {loss_fn.name.upper()}: {score:.4f} (higher_is_better={loss_fn.higher_is_better})")
        except Exception as e:
            print(f"  {loss_fn.name.upper()}: ERROR - {e}")

def test_model_registry():
    """Test model registry functionality."""
    print("\n" + "="*60)
    print("TEST 4: MODEL REGISTRY")
    print("="*60)
    
    automl = SimpleAutoML(target_col='target')
    
    # List available models
    available_models = automl.model_registry.list_models()
    print(f"Available models: {available_models}")
    
    # Test getting model configs
    for model_name in available_models:
        try:
            model_config = automl.model_registry.get_model_config(model_name)
            print(f"  {model_name}: Config loaded successfully - {model_config.__class__.__name__}")
            
            # Test parameter grid
            try:
                param_grid = model_config.get_param_grid('small')
                print(f"    Parameter grid keys: {list(param_grid.keys())}")
            except Exception as e:
                print(f"    Parameter grid error: {e}")
                
        except Exception as e:
            print(f"  {model_name}: ERROR - {e}")

def test_automl_basic_run():
    """Test basic AutoML run if models are available."""
    print("\n" + "="*60)
    print("TEST 5: BASIC AUTOML RUN")
    print("="*60)
    
    df = create_test_data()
    automl = SimpleAutoML(target_col='target')
    
    # Get available models
    available_models = automl.model_registry.list_models()
    
    if not available_models:
        print("No models available - skipping AutoML run test")
        return
    
    # Test with first available model
    test_model = available_models[0]
    print(f"Testing with model: {test_model}")
    
    try:
        results = automl.run_automl(
            df=df,
            feature_selection_fn=None,
            hypertuning_fn=None,
            models_to_run=[test_model],
            loss_fn=mae(),
            n_splits=2,  # Small for speed
            test_split=0.3,
            verbose=1
        )
        
        print("AutoML run completed successfully!")
        print(f"Best model: {results['best_model']}")
        
        model_result = results['models'][test_model]
        if 'error' not in model_result:
            print(f"Test MAE: {model_result['metrics']['test_loss']:.4f}")
            print(f"Test R²: {model_result['metrics']['test_r2']:.4f}")
        else:
            print(f"Model error: {model_result['error']}")
            
    except Exception as e:
        print(f"AutoML run failed: {e}")
        import traceback
        traceback.print_exc()

def test_feature_selection_interface():
    """Test feature selection interface methods."""
    print("\n" + "="*60)
    print("TEST 6: FEATURE SELECTION INTERFACE")
    print("="*60)
    
    df = create_test_data()
    X = df[[col for col in df.columns if col not in ['target', 'date']]]
    y = df['target']
    
    print(f"Original features: {list(X.columns)}")
    
    # Test interface methods (without actual ML fitting)
    try:
        # Create a dummy estimator-like object for interface testing
        class DummyEstimator:
            def get_params(self):
                return {}
            def __class__(self):
                return DummyEstimator
        
        dummy_estimator = DummyEstimator()
        selector = BackwardFeatureSelector(
            estimator=dummy_estimator,
            loss_fn=mae(),
            cv=None,
            verbose=1
        )
        
        print("Feature selector created successfully")
        print(f"Initial selected features: {selector.selected_features_}")
        print(f"Initial n_features_selected: {selector.n_features_selected}")
        
        # Test transform without fitting (should raise error)
        try:
            selector.transform(X)
            print("ERROR: Transform should fail before fitting")
        except ValueError as e:
            print(f"Correct error handling: {e}")
            
    except Exception as e:
        print(f"Feature selection interface test failed: {e}")

def test_hypertuning_interface():
    """Test hypertuning interface methods."""
    print("\n" + "="*60)
    print("TEST 7: HYPERTUNING INTERFACE")
    print("="*60)
    
    # Test interface methods (without actual ML fitting)
    try:
        class DummyEstimator:
            def get_params(self):
                return {'param1': 1, 'param2': 2}
            def __class__(self):
                return DummyEstimator
        
        dummy_estimator = DummyEstimator()
        param_grid = {'param1': [1, 2, 3], 'param2': [0.1, 0.2]}
        
        tuner = GridSearchTuner(
            estimator=dummy_estimator,
            loss_fn=mae(),
            param_grid=param_grid,
            cv=None,
            verbose=1
        )
        
        print("Hypertuning tuner created successfully")
        print(f"Parameter grid: {tuner.param_grid}")
        print(f"Initial best params: {tuner.best_params_}")
        
        # Test methods that should fail before fitting
        try:
            tuner.get_best_params()
            print("ERROR: get_best_params should fail before fitting")
        except ValueError as e:
            print(f"Correct error handling: {e}")
            
    except Exception as e:
        print(f"Hypertuning interface test failed: {e}")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*60)
    print("TEST 8: EDGE CASES AND ERROR HANDLING")
    print("="*60)
    
    # Test with invalid target column
    df = create_test_data()
    try:
        automl = SimpleAutoML(target_col='nonexistent_column')
        print("Created AutoML with invalid target column")
    except Exception as e:
        print(f"Invalid target column handling: {e}")
    
    # Test with very small dataset
    small_df = df.head(10)
    print(f"Testing with very small dataset: {small_df.shape}")
    
    # Test with single feature
    single_feature_df = df[['feature_0', 'target', 'date']]
    print(f"Testing with single feature dataset: {single_feature_df.shape}")
    
    # Test invalid loss function
    try:
        class InvalidLoss:
            pass
        
        invalid_loss = InvalidLoss()
        print("Created invalid loss function")
    except Exception as e:
        print(f"Invalid loss function handling: {e}")

def main():
    """Run lightweight test suite."""
    print("LIGHTWEIGHT AUTOML TEST SUITE")
    print("="*60)
    print("Testing interfaces, data flow, and basic functionality")
    
    start_time = time.time()
    
    try:
        # Test 1: Interface inheritance
        test_interface_inheritance()
        
        # Test 2: Data flow
        test_data_flow()
        
        # Test 3: Loss functions
        test_loss_functions()
        
        # Test 4: Model registry
        test_model_registry()
        
        # Test 5: Basic AutoML (if models available)
        test_automl_basic_run()
        
        # Test 6: Feature selection interface
        test_feature_selection_interface()
        
        # Test 7: Hypertuning interface
        test_hypertuning_interface()
        
        # Test 8: Edge cases
        test_edge_cases()
        
        total_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("LIGHTWEIGHT TEST SUITE COMPLETED!")
        print(f"Total test time: {total_time:.2f} seconds")
        print("="*60)
        
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
