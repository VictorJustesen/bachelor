import sys
import pandas as pd
import numpy as np

# Add the code directory to Python path
sys.path.append('/Users/victorjustesen/Desktop/skole/bachelor/bachelor/automltrainer/code')

# Import your AutoML components
from automl.automl import SimpleAutoML
from feature_selection.backwards import BackwardFeatureSelector
from hyper_tuning.grid_search import GridSearchTuner

# Create some sample data (or load your real data)
def create_sample_data():
    """Create sample regression data for testing"""
    np.random.seed(42)
    n_samples = 1000
    
    # Create features
    data = {
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(0, 1, n_samples),
        'feature_3': np.random.uniform(0, 10, n_samples),
        'feature_4': np.random.exponential(2, n_samples),
        'feature_5': np.random.normal(5, 2, n_samples),
        'noise_feature': np.random.normal(0, 0.1, n_samples),  # Should be removed by feature selection
    }
    
    # Create target (with some relationship to features)
    target = (2 * data['feature_1'] + 
             3 * data['feature_2'] + 
             0.5 * data['feature_3'] + 
             data['feature_4'] + 
             np.random.normal(0, 0.5, n_samples))
    
    data['purchase_price'] = target
    
    df = pd.DataFrame(data)
    return df

def test_automl_basic():
    """Test basic AutoML without feature selection or hypertuning"""
    print("=" * 60)
    print("TEST 1: Basic AutoML (No feature selection, No hypertuning)")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    print(f"Created sample data: {df.shape}")
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='purchase_price')
    
    # Run basic AutoML
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,      # No feature selection
        hypertuning_fn=None,           # No hypertuning
        n_splits=3,                    # Quick test with 3 splits
        test_split=0.2,
        verbose=1
    )
    
    print(f"\nBest model: {results['best_model']}")
    return automl, results

def test_automl_with_feature_selection():
    """Test AutoML with feature selection only"""
    print("\n" + "=" * 60)
    print("TEST 2: AutoML with Feature Selection")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='purchase_price')
    
    # Run AutoML with feature selection
    results = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,  # Use feature selection
        hypertuning_fn=None,                          # No hypertuning
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    print(f"\nBest model: {results['best_model']}")
    print(f"Features selected: {results['data_info']}")
    return automl, results

def test_automl_with_hypertuning():
    """Test AutoML with hypertuning only"""
    print("\n" + "=" * 60)
    print("TEST 3: AutoML with Hypertuning")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='purchase_price')
    
    # Run AutoML with hypertuning
    results = automl.run_automl(
        df=df,
        feature_selection_fn=None,                # No feature selection
        hypertuning_fn=GridSearchTuner,          # Use hypertuning
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    print(f"\nBest model: {results['best_model']}")
    return automl, results

def test_automl_full():
    """Test full AutoML with both feature selection and hypertuning"""
    print("\n" + "=" * 60)
    print("TEST 4: Full AutoML (Feature Selection + Hypertuning)")
    print("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize AutoML
    automl = SimpleAutoML(target_col='purchase_price')
    
    # Run full AutoML
    results = automl.run_automl(
        df=df,
        feature_selection_fn=BackwardFeatureSelector,  # Use feature selection
        hypertuning_fn=GridSearchTuner,               # Use hypertuning
        n_splits=3,
        test_split=0.2,
        verbose=1
    )
    
    print(f"\nBest model: {results['best_model']}")
    print(f"Data info: {results['data_info']}")
    
    # Show detailed results for each model
    print("\nDetailed Results:")
    for model_name, result in results['models'].items():
        if 'error' not in result:
            print(f"{model_name}:")
            print(f"  Features used: {result['n_features_selected']}/{result['original_features']}")
            print(f"  Test RMSE: {result['metrics']['test_rmse']:.4f}")
            print(f"  Test R²: {result['metrics']['test_r2']:.4f}")
            if 'cv_score' in result:
                print(f"  CV Score: {result['cv_score']:.4f}")
    
    return automl, results


if __name__ == "__main__":
    print("Testing AutoML System")
    print("=" * 60)
    
    # Run all tests
    try:
        # Test 1: Basic
        automl1, results1 = test_automl_basic()
        
        # Test 2: With feature selection
        automl2, results2 = test_automl_with_feature_selection()
        
        # Test 3: With hypertuning
        automl3, results3 = test_automl_with_hypertuning()
        
        # Test 4: Full AutoML
        automl4, results4 = test_automl_full()
        
        # Test 5: Real data (modify as needed)
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()