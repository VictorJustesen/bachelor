"""
Comprehensive test suite for the AutoML system.

This test systematically evaluates:
1. All available models
2. All loss functions  
3. All hypertuning methods (including None)
4. All feature selection methods (including None)
5. Different combinations to ensure system robustness
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
    n_samples = 50000  # Smaller dataset for faster testing
    n_features = 8
    
    # Create features with different scales and patterns
    X = pd.DataFrame({
        'feature_0': np.random.normal(0, 1, n_samples),
        'feature_1': np.random.normal(10, 5, n_samples),
        'feature_2': np.random.exponential(2, n_samples),
        'feature_3': np.random.uniform(-5, 5, n_samples),
        'feature_4': np.random.normal(0, 0.1, n_samples),  # Low variance
        'feature_5': np.random.normal(100, 50, n_samples),  # High scale
        'feature_6': np.random.binomial(1, 0.3, n_samples),  # Binary
        'feature_7': np.random.poisson(3, n_samples)  # Count data
    })
    
    # Create target with specific dependencies (features 0, 1, 2 are important)
    y = (3 * X['feature_0'] + 
         0.5 * X['feature_1'] - 
         2 * X['feature_2'] + 
         0.1 * X['feature_3'] +
         np.random.normal(0, 1, n_samples))
    
    # Combine into DataFrame
    df = X.copy()
    df['target'] = y
    df['date'] = pd.date_range('2020-01-01', periods=n_samples, freq='D')
    
    return df

def test_all_models_basic():
    """Test all models with basic configuration (no feature selection, no hypertuning)."""
    print("\n" + "="*80)
    print("TEST 1: ALL MODELS - BASIC CONFIGURATION")
    print("="*80)
    
    df = create_test_data()
    automl = SimpleAutoML(target_col='target')
    
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=None,
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    print(f"\nRESULTS SUMMARY:")
    print(f"Best model: {results['best_model']}")
    for model_name, model_result in results['models'].items():
        if 'error' not in model_result:
            print(f"  {model_name:15s} | MAE: {model_result['metrics']['test_loss']:.3f} ")
        else:
            print(f"  {model_name:15s} | ERROR: {model_result['error']}")
    
    return results

def test_loss_functions():
    """Test different loss functions with same model."""
    print("\n" + "="*80)
    print("TEST 2: DIFFERENT LOSS FUNCTIONS - LIGHTGBM MODEL")
    print("="*80)
    
    df = create_test_data()
    loss_functions = [mae(), mape(), rmse()]
    
    for loss_fn in loss_functions:
        print(f"\n--- Testing {loss_fn.name.upper()} Loss Function ---")
        
        automl = SimpleAutoML(target_col='target')
        results = automl.run_automl(
            df=df,
            feature_selection_fn=None,
            hypertuning_fn=None,
            models_to_run=['xgboost'],
            loss_fn=loss_fn,
            n_splits=3,
            test_split=0.2,
            verbose=0
        )
        
        model_result = results['models']['xgboost']
        if 'error' not in model_result:
            print(f"  Test {loss_fn.name.upper()}: {model_result['metrics']['test_loss']:.4f}")
        else:
            print(f"  ERROR: {model_result['error']}")

def test_hypertuning_methods():
    """Test different hypertuning methods with same model and loss function."""
    print("\n" + "="*80)
    print("TEST 3: DIFFERENT HYPERTUNING METHODS - LIGHTGBM + MAE")
    print("="*80)
    
    df = create_test_data()
    hypertuning_methods = [
        (None, "No Hypertuning"),
        (GridSearchTuner, "Grid Search"),
        (LineSearchTuner, "Line Search")
    ]
    
    for tuner_class, tuner_name in hypertuning_methods:
        print(f"\n--- Testing {tuner_name} ---")
        start_time = time.time()
        
        automl = SimpleAutoML(target_col='target')
        results = automl.run_automl(
            df=df,
            feature_selection_fn=None,
            hypertuning_fn=tuner_class,
            models_to_run=['lightgbm'],
            loss_fn=mae(),
            n_splits=3,
            test_split=0.2,
            param_amount='small',
            verbose=1
        )
        
        elapsed_time = time.time() - start_time
        model_result = results['models']['lightgbm']
        
        if 'error' not in model_result:
            print(f"  Test MAE: {model_result['metrics']['test_loss']:.4f}")
            print(f"  Time taken: {elapsed_time:.2f}s")
            if 'cv_score' in model_result:
                print(f"  CV Score: {model_result['cv_score']:.4f}")
        else:
            print(f"  ERROR: {model_result['error']}")

def test_feature_selection_methods():
    """Test different feature selection methods with same model and hypertuning."""
    print("\n" + "="*80)
    print("TEST 4: DIFFERENT FEATURE SELECTION METHODS - LIGHTGBM + GRID SEARCH + MAE")
    print("="*80)
    
    df = create_test_data()
    feature_selection_methods = [
        (None, "No Feature Selection"),
        (BackwardFeatureSelector, "Backward Selection")
    ]
    
    for selector_class, selector_name in feature_selection_methods:
        print(f"\n--- Testing {selector_name} ---")
        start_time = time.time()
        
        automl = SimpleAutoML(target_col='target')
        results = automl.run_automl(
            df=df,
            feature_selection_fn=selector_class,
            hypertuning_fn=GridSearchTuner,
            models_to_run=['lightgbm'],
            loss_fn=mae(),
            n_splits=3,
            test_split=0.2,
            param_amount='small',
            verbose=1
        )
        
        elapsed_time = time.time() - start_time
        model_result = results['models']['lightgbm']
        
        if 'error' not in model_result:
            print(f"  Features: {model_result['n_features_selected']}/{model_result['original_features']}")
            print(f"  Test MAE: {model_result['metrics']['test_loss']:.4f}")
            print(f"  Time taken: {elapsed_time:.2f}s")
            if 'cv_score' in model_result:
                print(f"  CV Score: {model_result['cv_score']:.4f}")
        else:
            print(f"  ERROR: {model_result['error']}")

def test_model_combinations():
    """Test different models with same configuration."""
    print("\n" + "="*80)
    print("TEST 5: DIFFERENT MODELS - BACKWARD SELECTION + GRID SEARCH + RMSE")
    print("="*80)
    
    df = create_test_data()
    models_to_test = ['lightgbm', 'xgboost']  # Test available models individually
    
    for model_name in models_to_test:
        print(f"\n--- Testing {model_name.upper()} Model ---")
        start_time = time.time()
        
        try:
            automl = SimpleAutoML(target_col='target')
            results = automl.run_automl(
                df=df,
                feature_selection_fn=BackwardFeatureSelector,
                hypertuning_fn=GridSearchTuner,
                models_to_run=[model_name],
                loss_fn=rmse(),
                n_splits=3,
                test_split=0.2,
                param_amount='small',
                verbose=1
            )
            
            elapsed_time = time.time() - start_time
            model_result = results['models'][model_name]
            
            if 'error' not in model_result:
                print(f"  Features: {model_result['n_features_selected']}/{model_result['original_features']}")
                print(f"  Test RMSE: {model_result['metrics']['test_loss']:.4f}")
                print(f"  Time taken: {elapsed_time:.2f}s")
                if 'cv_score' in model_result:
                    print(f"  CV Score: {model_result['cv_score']:.4f}")
            else:
                print(f"  ERROR: {model_result['error']}")
                
        except Exception as e:
            print(f"  FAILED: {str(e)}")

def test_full_combinations():
    """Test a few key combinations of all components."""
    print("\n" + "="*80)
    print("TEST 6: FULL COMBINATIONS - COMPREHENSIVE TEST")
    print("="*80)
    
    df = create_test_data()
    
    test_combinations = [
        # (feature_selection, hypertuning, models, loss, description)
        (None, None, ['lightgbm'], mae(), "Baseline: No FS, No HT"),
        (BackwardFeatureSelector, None, ['lightgbm'], mae(), "Feature Selection Only"),
        (None, GridSearchTuner, ['lightgbm'], mae(), "Hypertuning Only"),
        (BackwardFeatureSelector, GridSearchTuner, ['lightgbm'], mae(), "Full Pipeline"),
        (None, LineSearchTuner, ['xgboost'], rmse(), "XGBoost + Line Search + RMSE"),
    ]
    
    for i, (fs_method, ht_method, models, loss_fn, description) in enumerate(test_combinations, 1):
        print(f"\n--- Combination {i}: {description} ---")
        start_time = time.time()
        
        try:
            automl = SimpleAutoML(target_col='target')
            results = automl.run_automl(
                df=df,
                feature_selection_fn=fs_method,
                hypertuning_fn=ht_method,
                models_to_run=models,
                loss_fn=loss_fn,
                n_splits=3,
                test_split=0.2,
                param_amount='small',
                verbose=0  # Reduce verbosity for combinations
            )
            
            elapsed_time = time.time() - start_time
            best_model = results['best_model']
            model_result = results['models'][best_model]
            
            if 'error' not in model_result:
                print(f"  Model: {best_model}")
                if 'n_features_selected' in model_result:
                    print(f"  Features: {model_result['n_features_selected']}/{model_result['original_features']}")
                print(f"  Test {loss_fn.name.upper()}: {model_result['metrics']['test_loss']:.4f}")
                print(f"  Time: {elapsed_time:.2f}s")
            else:
                print(f"  ERROR: {model_result['error']}")
                
        except Exception as e:
            print(f"  FAILED: {str(e)}")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*80)
    print("TEST 7: EDGE CASES AND ERROR HANDLING")
    print("="*80)
    
    df = create_test_data()
    
    edge_cases = [
        # Test with very small data
        (df.head(50), "Small dataset (50 samples)"),
        # Test with single feature (after removing some)
        (df[['feature_0', 'target', 'date']], "Single feature dataset"),
    ]
    
    for test_df, description in edge_cases:
        print(f"\n--- Testing: {description} ---")
        
        try:
            automl = SimpleAutoML(target_col='target')
            results = automl.run_automl(
                df=test_df,
                feature_selection_fn=None,  # Skip feature selection for edge cases
                hypertuning_fn=None,        # Skip hypertuning for speed
                models_to_run=['lightgbm'],
                loss_fn=mae(),
                n_splits=2,  # Reduced splits for small data
                test_split=0.3,
                verbose=0
            )
            
            model_result = results['models']['lightgbm']
            if 'error' not in model_result:
                print(f"  SUCCESS: Test MAE: {model_result['metrics']['test_loss']:.4f}")
            else:
                print(f"  ERROR: {model_result['error']}")
                
        except Exception as e:
            print(f"  EXCEPTION: {str(e)}")

def main():
    """Run comprehensive test suite."""
    print("COMPREHENSIVE AUTOML TEST SUITE")
    print("="*80)
    print("Testing all combinations of models, hypertuning, feature selection, and loss functions")
    
    start_time = time.time()
    
    try:
        # Test 1: Basic model comparison
        test_all_models_basic()
        
        # Test 2: Loss function comparison
        test_loss_functions()
        
        # Test 3: Hypertuning method comparison
        test_hypertuning_methods()
        
        # Test 4: Feature selection comparison
        test_feature_selection_methods()
        
        # Test 5: Model comparison with full pipeline
        test_model_combinations()
        
        # Test 6: Full combinations
        test_full_combinations()
        
        # Test 7: Edge cases
        test_edge_cases()
        
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"Total test time: {total_time:.2f} seconds")
        print("="*80)
        
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
