"""
Simple linear regression example with real data and model saving.
No feature selection, no hypertuning - just basic linear regression.
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
    """Simple linear regression example."""
    print("SIMPLE LINEAR REGRESSION EXAMPLE")
    print("="*50)
    
    # Load the data
    data_path = Path(__file__).parent.parent / 'data' / 'realdata' / 'cleaned_data_harsh.csv'
    print(f"Loading data from: {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"Original data shape: {df.shape}")
    
    # Remove the 'dato' column
    df_clean = df.drop(columns=['dato'])
    print(f"Cleaned data shape: {df_clean.shape}")
    
    # Initialize AutoML with target column 'Købesum'
    automl = SimpleAutoML(target_col='Købesum')
    
    # Run AutoML with just linear regression
    print("\nRunning linear regression...")
    results = automl.run_automl(
        df=df_clean,
        feature_selection_fn=None,      # No feature selection
        hypertuning_fn=None,            # No hypertuning
        models_to_run=['linear_regression'],  # Just linear regression
        loss_fn=mae(),
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    # Print results
    lr_result = results['models']['linear_regression']
    if 'error' not in lr_result:
        print(f"\nLinear Regression Results:")
        print(f"  Test MAE: {lr_result['metrics']['test_loss']:,.2f}")
        print(f"  Train MAE: {lr_result['metrics']['train_loss']:,.2f}")
        print(f"  Features used: {lr_result['n_features_selected']}")
        
        # Create saved_models directory if it doesn't exist
        save_dir = Path(__file__).parent / 'saved_models'
        save_dir.mkdir(exist_ok=True)
        
        # Save the model
        model_path = save_dir / 'simple_linear_regression'
        save_path = automl.save_model(str(model_path))
        print(f"  Model saved to: {save_path}")
        
        print("\nDone! ✓")
        
    else:
        print(f"Error: {lr_result['error']}")

if __name__ == "__main__":
    main()
