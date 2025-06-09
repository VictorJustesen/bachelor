import sys
import pandas as pd
import numpy as np
from pathlib import Path
from functools import partial # <-- Add this import


# Add the code directory to Python path
code_dir = Path(__file__).parent.parent / 'code'
sys.path.append(str(code_dir))

# Add the Loss directory to path
loss_dir = Path(__file__).parent.parent / 'Loss'
sys.path.append(str(loss_dir))

# Import your AutoML components
from automl.automl import SimpleAutoML
from hyper_tuning.line_search import LineSearchTuner
from mape import mape  # Import from Loss directory

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
    print("RUN 1: SIMPLE (No extras, RMSE)")
    print("="*50)

    automl = SimpleAutoML(target_col='Købesum')
    tuner_with_passes = partial(LineSearchTuner, max_passes=2)

    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=tuner_with_passes,
        loss_fn=mape(),
        n_splits=5,
        test_split=0.05,
        verbose=1
    )

    return results

def line_search_mape_run(df):
    """Run 2: Line Search with MAPE loss on specific models"""
    print("\n" + "="*50)
    print("RUN 2: Line Search (MAPE, XGBoost vs LightGBM)")
    print("="*50)

    automl = SimpleAutoML(target_col='Købesum')

    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,
        hypertuning_fn=LineSearchTuner(max_passes=2),
        loss_fn=mape(),
        models_to_run=['lightgbm', 'XGboost'], # Run only these models
        n_splits=3,
        test_split=0.01,
        verbose=1,
        param_amount='custom'
    )

    return results

def main():
    # Load data
    df = load_cleaned_data()

    # Run 1: Simple
    simple_results = simple_run(df)
    simple_best_model = simple_results['best_model']
    simple_loss = simple_results['models'][simple_best_model]['metrics']['test_loss']

    # Run 2: Line Search with MAPE
    line_search_results = line_search_mape_run(df)
    line_search_best_model = line_search_results['best_model']
    line_search_loss = line_search_results['models'][line_search_best_model]['metrics']['test_loss']

    # Compare
    print("\n" + "="*60)
    print("COMPARISON OF RUNS")
    print("="*60)
    print(f"Simple Run Best Model:      '{simple_best_model}' with test_loss: {simple_loss:,.2f}")
    print(f"Line Search Run Best Model: '{line_search_best_model}' with test_loss: {line_search_loss:,.2f}")

if __name__ == "__main__":
    main()