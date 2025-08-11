
import sys
import pandas as pd
from pathlib import Path

#the import process will be different if made like a true library
code = Path(__file__).parent/'code'
sys.path.append(str(code))
from automl.automl import SimpleAutoML
from Loss import mae



# Load the data
data_path =  'cleaned_data_harsh.csv'

df = pd.read_csv(data_path)
df = df.sample(frac=0.1, random_state=42) 

df_clean = df.drop(columns=['dato'])
print(f"Cleaned data shape: {df_clean.shape}")

automl = SimpleAutoML()
models_to_run=['linear_regression', 'xgboost']
# Run AutoML with just linear regression
print("\nRunning linear regression...")
results = automl.run_automl( df=df_clean,
    target_col='Købesum',
    feature_selection_fn=None,
    models_to_run=models_to_run,
    hypertuning_fn=None,
    loss_fn=mae(),
    n_splits=5,
    test_split=0.2,
    verbose=1)

save_dir = Path(__file__).parent/'saved_models'
save_dir.mkdir(exist_ok=True)

model_path = save_dir/'Deenaexample'
save_path = automl.save_model(str(model_path))
    

