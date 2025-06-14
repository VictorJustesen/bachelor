"""
Test model saving for different model types: Linear Regression, XGBoost, and LightGBM.
"""

import sys
import pandas as pd
from pathlib import Path

# Add the code directory to Python path
code_dir = Path(__file__).parent / 'code'
sys.path.append(str(code_dir))

# Import the AutoML components
from automl.automl import SimpleAutoML
from Loss import mae

def main():
    """Test model saving for different model types."""
    print("MODEL SAVING TEST")
    print("="*50)
    
    # Load the data
    data_path = Path(__file__).parent.parent / 'data' / 'realdata' / 'cleaned_data_harsh.csv'
    print(f"Loading data from: {data_path}")
    
    df = pd.read_csv(data_path)
    # Remove the 'dato' column and take a smaller sample for faster testing
    df_clean = df.drop(columns=['dato']).sample(n=10000, random_state=42)
    print(f"Using sample data shape: {df_clean.shape}")
    
    # Test each model type
    models_to_test = ['linear_regression', 'xgboost', 'lightgbm']
    
    for model_name in models_to_test:
        print(f"\n--- Testing {model_name.upper()} ---")
        
        # Initialize AutoML
        automl = SimpleAutoML(target_col='Købesum')
        
        # Run AutoML with the specific model
        results = automl.run_automl(
            df=df_clean,
            feature_selection_fn=None,
            hypertuning_fn=None,
            models_to_run=[model_name],
            loss_fn=mae(),
            n_splits=3,
            test_split=0.2,
            verbose=0
        )
        
        # Check results
        model_result = results['models'][model_name]
        if 'error' not in model_result:
            print(f"  Test MAE: {model_result['metrics']['test_loss']:,.2f}")
            
            # Save the model
            save_dir = Path(__file__).parent / 'saved_models'
            save_dir.mkdir(exist_ok=True)
            model_path = save_dir / f'{model_name}_test'
            
            try:
                save_path = automl.save_model(str(model_path))
                print(f"  ✓ Model saved successfully to: {save_path}")
                
                # Check what files were created
                files_created = list(save_dir.glob(f'{model_name}_test*'))
                print(f"  Files created: {[f.name for f in files_created]}")
                
            except Exception as e:
                print(f"  ✗ Model saving failed: {e}")
        else:
            print(f"  ✗ Model training failed: {model_result['error']}")
    
    print(f"\n{'='*50}")
    print("MODEL SAVING TEST COMPLETED!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
