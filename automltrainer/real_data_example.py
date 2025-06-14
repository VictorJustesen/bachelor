"""
Example script using real data with linear regression and model saving.

This example:
1. Loads the real data from cleaned_data_harsh.csv
2. Removes non-numerical columns (dato)
3. Runs AutoML with linear regression
4. Saves the trained model for later use
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
from feature_selection import BackwardFeatureSelector
from hyper_tuning import GridSearchTuner
from Loss import mae, rmse

def load_and_clean_data():
    """Load the real data and remove non-numerical columns."""
    # Load the data
    data_path = Path(__file__).parent.parent / 'data' / 'realdata' / 'cleaned_data_harsh.csv'
    print(f"Loading data from: {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"Original data shape: {df.shape}")
    print(f"Original columns: {list(df.columns)}")
    
    # Remove the 'dato' column (date column)
    columns_to_remove = ['dato']
    
    # Check if there are any other non-numerical columns
    non_numerical_cols = []
    for col in df.columns:
        if col not in columns_to_remove and col != 'Købesum':  # Skip target column
            try:
                pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError):
                non_numerical_cols.append(col)
    
    if non_numerical_cols:
        print(f"Found additional non-numerical columns: {non_numerical_cols}")
        columns_to_remove.extend(non_numerical_cols)
    
    # Remove non-numerical columns
    df_clean = df.drop(columns=columns_to_remove)
    print(f"Removed columns: {columns_to_remove}")
    print(f"Cleaned data shape: {df_clean.shape}")
    print(f"Remaining columns: {list(df_clean.columns)}")
    
    # Check for any missing values
    missing_values = df_clean.isnull().sum()
    if missing_values.any():
        print(f"Missing values found:")
        print(missing_values[missing_values > 0])
        # Drop rows with missing values
        df_clean = df_clean.dropna()
        print(f"Data shape after removing missing values: {df_clean.shape}")
    
    return df_clean

def test_linear_regression_basic():
    """Test linear regression with basic configuration."""
    print("\n" + "="*80)
    print("LINEAR REGRESSION - BASIC CONFIGURATION (NO FEATURE SELECTION, NO HYPERTUNING)")
    print("="*80)
    
    df = load_and_clean_data()
    
    # Initialize AutoML with correct target column
    automl = SimpleAutoML(target_col='Købesum')
    
    start_time = time.time()
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=None,
        models_to_run=['linear_regression'],  # Only run linear regression
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    elapsed_time = time.time() - start_time
    
    # Print results
    lr_result = results['models']['linear_regression']
    if 'error' not in lr_result:
        print(f"\nLinear Regression Results:")
        print(f"  Test MAE: {lr_result['metrics']['test_loss']:,.2f}")
        print(f"  Train MAE: {lr_result['metrics']['train_loss']:,.2f}")
        print(f"  Features used: {lr_result['n_features_selected']}")
        print(f"  Training time: {elapsed_time:.2f}s")
        
        # Save the model
        model_path = Path(__file__).parent / 'saved_models' / 'linear_regression_basic'
        save_path = automl.save_model(str(model_path))
        print(f"  Model saved to: {save_path}")
        
    else:
        print(f"Error: {lr_result['error']}")
    
    return results

def test_linear_regression_with_feature_selection():
    """Test linear regression with feature selection."""
    print("\n" + "="*80)
    print("LINEAR REGRESSION - WITH BACKWARD FEATURE SELECTION")
    print("="*80)
    
    df = load_and_clean_data()
    
    automl = SimpleAutoML(target_col='Købesum')
    
    start_time = time.time()
    results = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,
        hypertuning_fn=None,
        models_to_run=['linear_regression'],
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    elapsed_time = time.time() - start_time
    
    # Print results
    lr_result = results['models']['linear_regression']
    if 'error' not in lr_result:
        print(f"\nLinear Regression with Feature Selection Results:")
        print(f"  Test MAE: {lr_result['metrics']['test_loss']:,.2f}")
        print(f"  Train MAE: {lr_result['metrics']['train_loss']:,.2f}")
        print(f"  Features selected: {lr_result['n_features_selected']}/{lr_result['original_features']}")
        print(f"  Training time: {elapsed_time:.2f}s")
        
        # Save the model
        model_path = Path(__file__).parent / 'saved_models' / 'linear_regression_feature_selection'
        save_path = automl.save_model(str(model_path))
        print(f"  Model saved to: {save_path}")
        
    else:
        print(f"Error: {lr_result['error']}")
    
    return results

def test_linear_regression_full_pipeline():
    """Test linear regression with feature selection and hypertuning."""
    print("\n" + "="*80)
    print("LINEAR REGRESSION - FULL PIPELINE (FEATURE SELECTION + HYPERTUNING)")
    print("="*80)
    
    df = load_and_clean_data()
    
    automl = SimpleAutoML(target_col='Købesum')
    
    start_time = time.time()
    results = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,
        hypertuning_fn=GridSearchTuner,
        models_to_run=['linear_regression'],
        loss_fn=rmse(),  # Use RMSE for this test
        n_splits=3,
        test_split=0.2,
        param_amount='small',  # Use small parameter grid for faster execution
        verbose=1
    )
    elapsed_time = time.time() - start_time
    
    # Print results
    lr_result = results['models']['linear_regression']
    if 'error' not in lr_result:
        print(f"\nLinear Regression Full Pipeline Results:")
        print(f"  Test RMSE: {lr_result['metrics']['test_loss']:,.2f}")
        print(f"  Train RMSE: {lr_result['metrics']['train_loss']:,.2f}")
        print(f"  Features selected: {lr_result['n_features_selected']}/{lr_result['original_features']}")
        if 'cv_score' in lr_result:
            print(f"  CV Score: {lr_result['cv_score']:,.2f}")
        print(f"  Best parameters: {lr_result['params']}")
        print(f"  Training time: {elapsed_time:.2f}s")
        
        # Save the model
        model_path = Path(__file__).parent / 'saved_models' / 'linear_regression_full_pipeline'
        save_path = automl.save_model(str(model_path))
        print(f"  Model saved to: {save_path}")
        
    else:
        print(f"Error: {lr_result['error']}")
    
    return results

def compare_all_models():
    """Compare linear regression with other models on the real data."""
    print("\n" + "="*80)
    print("MODEL COMPARISON - ALL MODELS ON REAL DATA")
    print("="*80)
    
    df = load_and_clean_data()
    
    automl = SimpleAutoML(target_col='Købesum')
    
    start_time = time.time()
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,  # No feature selection for fair comparison
        hypertuning_fn=None,        # No hypertuning for speed
        models_to_run=None,         # Run all available models
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    elapsed_time = time.time() - start_time
    
    print(f"\nModel Comparison Results:")
    print(f"Best model: {results['best_model']}")
    for model_name, model_result in results['models'].items():
        if 'error' not in model_result:
            print(f"  {model_name:15s} | Test MAE: {model_result['metrics']['test_loss']:,.2f}")
        else:
            print(f"  {model_name:15s} | ERROR: {model_result['error']}")
    
    print(f"Total comparison time: {elapsed_time:.2f}s")
    
    # Save the best model
    model_path = Path(__file__).parent / 'saved_models' / f'best_model_{results["best_model"]}'
    save_path = automl.save_model(str(model_path))
    print(f"Best model saved to: {save_path}")
    
    return results

def main():
    """Run all linear regression examples with real data."""
    print("REAL DATA LINEAR REGRESSION EXAMPLES")
    print("="*80)
    print("Using cleaned_data_harsh.csv with target column 'Købesum'")
    
    # Create saved_models directory
    save_dir = Path(__file__).parent / 'saved_models'
    save_dir.mkdir(exist_ok=True)
    
    try:
        # Test 1: Basic linear regression
        test_linear_regression_basic()
        
        # Test 2: Linear regression with feature selection
        test_linear_regression_with_feature_selection()
        
        # Test 3: Linear regression full pipeline
        test_linear_regression_full_pipeline()
        
        # Test 4: Compare with other models
        compare_all_models()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("Check the 'saved_models' directory for saved model files.")
        print("="*80)
        
    except Exception as e:
        print(f"\nEXAMPLE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
