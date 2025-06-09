import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add the code directory to Python path
sys.path.append('/Users/victorjustesen/Desktop/skole/bachelor/bachelor/automltrainer/code')

# Import your AutoML components
from automl.automl import SimpleAutoML
from feature_selection.backwards import BackwardFeatureSelector
from hyper_tuning.grid_search import GridSearchTuner

def load_cleaned_data():
    """Load your cleaned real estate data"""
    
  
    df = pd.read_csv('/Users/victorjustesen/Desktop/skole/bachelor/bachelor/dataexplor/cleaned_data_harsh.csv')
    
    if 'dato' in df.columns:
        df['dato'] = pd.to_datetime(df['dato'])
        df = df.set_index('dato')
    
    df = df.sort_index()
    print(f"Data loaded: {df.shape}")
    return df

def simple_run(df):
    """Run 1: Basic AutoML - No feature selection, no hypertuning"""
    print("\n" + "="*50)
    print("RUN 1: SIMPLE (No extras)")
    print("="*50)
    
    automl = SimpleAutoML(target_col='Købesum')
    
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,      # Nothing
        hypertuning_fn=None,           # Nothing
        n_splits=3,
        test_split=0.01,
        verbose=1
    )
    
    return results

def full_run(df):
    """Run 2: Full AutoML - Everything enabled"""
    print("\n" + "="*50)
    print("RUN 2: FULL (Everything)")
    print("="*50)
    
    automl = SimpleAutoML(target_col='Købesum')
    
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,  # Feature selection
        hypertuning_fn=GridSearchTuner,               # Hypertuning
        n_splits=3,
        test_split=0.01,
        verbose=1,
        param_amount='custom'  # Use full parameter grid
    )
    
    return results

def main():
    # Load data
    df = load_cleaned_data()
    # Run 1: Simple
    simple_results = simple_run(df)
    simple_rmse = simple_results['models'][simple_results['best_model']]['metrics']['test_loss']
    
    # Run 2: Full
    full_results = full_run(df)
    full_rmse = full_results['models'][full_results['best_model']]['metrics']['test_loss']

    # Compare
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    print(f"Simple run best RMSE:  {simple_rmse:,.2f} DKK")
    print(f"Full run best RMSE:    {full_rmse:,.2f} DKK")
    improvement = ((simple_rmse - full_rmse) / simple_rmse) * 100
    print(f"Improvement:           {improvement:+.2f}%")
        
  

if __name__ == "__main__":
    main()