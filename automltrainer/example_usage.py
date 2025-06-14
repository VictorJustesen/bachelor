"""
Example usage of the AutoML system with interfaces for feature selection and hypertuning.

This example demonstrates:
1. How to use different feature selection methods through the FeatureSelectionInterface
2. How to use different hypertuning methods through the HypertuningInterface
3. How to create custom implementations of these interfaces
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add the code directory to Python path
code_dir = Path(__file__).parent / 'code'
sys.path.append(str(code_dir))

# Import the AutoML components and interfaces
from automl.automl import SimpleAutoML
from feature_selection import BackwardFeatureSelector, FeatureSelectionInterface
from hyper_tuning import GridSearchTuner, LineSearchTuner, HypertuningInterface
from Loss import mae, mape, rmse

def create_sample_data():
    """Create sample regression data for demonstration."""
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    # Create features
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Create target with some noise and feature dependencies
    y = (2 * X['feature_0'] + 
         1.5 * X['feature_1'] - 
         0.5 * X['feature_2'] + 
         np.random.randn(n_samples) * 0.1)
    
    # Combine into DataFrame
    df = X.copy()
    df['target'] = y
    df['date'] = pd.date_range('2020-01-01', periods=n_samples, freq='D')
    
    return df

def demonstrate_feature_selection_interface():
    """Demonstrate how to use feature selection with the interface."""
    print("\n" + "="*60)
    print("DEMONSTRATING FEATURE SELECTION INTERFACE")
    print("="*60)
    
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='target')
    
    # Example 1: Using BackwardFeatureSelector
    print("\n1. Using BackwardFeatureSelector:")
    results1 = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,
        hypertuning_fn=None,
        models_to_run=['lightgbm'],  # Use single model for speed
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    best_model_info = results1['models'][results1['best_model']]
    print(f"Features selected: {best_model_info['n_features_selected']}/{best_model_info['original_features']}")
    print(f"Test MAE: {best_model_info['metrics']['test_loss']:.4f}")

def demonstrate_hypertuning_interface():
    """Demonstrate how to use hypertuning with the interface."""
    print("\n" + "="*60)
    print("DEMONSTRATING HYPERTUNING INTERFACE")
    print("="*60)
    
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='target')
    
    # Example 1: Using GridSearchTuner
    print("\n1. Using GridSearchTuner:")
    results1 = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=GridSearchTuner,
        models_to_run=['lightgbm'],
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        param_amount='small',
        verbose=1
    )
    
    best_model_info = results1['models'][results1['best_model']]
    print(f"Test MAE: {best_model_info['metrics']['test_loss']:.4f}")
    
    # Example 2: Using LineSearchTuner
    print("\n2. Using LineSearchTuner:")
    results2 = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=LineSearchTuner,
        models_to_run=['lightgbm'],
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        param_amount='small',
        verbose=1
    )
    
    best_model_info = results2['models'][results2['best_model']]
    print(f"Test MAE: {best_model_info['metrics']['test_loss']:.4f}")

def demonstrate_combined_usage():
    """Demonstrate using both feature selection and hypertuning together."""
    print("\n" + "="*60)
    print("DEMONSTRATING COMBINED FEATURE SELECTION + HYPERTUNING")
    print("="*60)
    
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='target')
    
    # Use both feature selection and hypertuning
    results = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,
        hypertuning_fn=GridSearchTuner,
        models_to_run=['lightgbm', 'xgboost'],
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        param_amount='small',
        verbose=1
    )
    
    print(f"\nBest model: {results['best_model']}")
    
    # Show results for each model
    for model_name, model_result in results['models'].items():
        if 'error' not in model_result:
            print(f"\n{model_name}:")
            print(f"  Features: {model_result['n_features_selected']}/{model_result['original_features']}")
            print(f"  Test MAE: {model_result['metrics']['test_loss']:.4f}")
            print(f"  Test R²: {model_result['metrics']['test_r2']:.4f}")

def demonstrate_different_loss_functions():
    """Demonstrate using different loss functions."""
    print("\n" + "="*60)
    print("DEMONSTRATING DIFFERENT LOSS FUNCTIONS")
    print("="*60)
    
    df = create_sample_data()
    automl = SimpleAutoML(target_col='target')
    
    # Test different loss functions
    loss_functions = [mae(), mape(), rmse()]
    
    for loss_fn in loss_functions:
        print(f"\nUsing {loss_fn.name.upper()} loss function:")
        results = automl.run_automl(
            df=df,
            feature_selection_fn=None,
            hypertuning_fn=None,
            models_to_run=['lightgbm'],
            loss_fn=loss_fn,
            n_splits=3,
            test_split=0.2,
            verbose=0
        )
        
        best_model_info = results['models'][results['best_model']]
        print(f"  Test {loss_fn.name.upper()}: {best_model_info['metrics']['test_loss']:.4f}")

def main():
    """Run all demonstrations."""
    print("AutoML Interface Demonstration")
    print("==============================")
    
    try:
        # Test 1: Feature Selection Interface
        demonstrate_feature_selection_interface()
        
        # Test 2: Hypertuning Interface
        demonstrate_hypertuning_interface()
        
        # Test 3: Combined Usage
        demonstrate_combined_usage()
        
        # Test 4: Different Loss Functions
        demonstrate_different_loss_functions()
        
        print("\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
