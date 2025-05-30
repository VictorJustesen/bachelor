import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
# from sklearn.linear_model import LinearRegression # Original, commented out
from sklearn.ensemble import RandomForestRegressor
# from xgboost import XGBRegressor # Original, commented out
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import autosklearn.regression
import autosklearn.metrics # For specifying metric
import shutil # For managing temp folders if needed

# 1. locate all cleaned Parquet files
data_dir = Path(__file__).resolve().parent / "Housing_data_cleaned"
parquet_files = sorted(data_dir.glob("DKHousingprices_*.parquet"))

if not parquet_files:
    raise FileNotFoundError(f"No Parquet files found in {data_dir}. Please check the path: {data_dir.resolve()}")

# 2. read each into a DataFrame
df_list = [pd.read_parquet(p, engine="pyarrow") for p in parquet_files]

# 3. concatenate into one DataFrame
df = pd.concat(df_list, ignore_index=True)
print("Initial columns:", df.columns.tolist())

# 4. convert date to datetime and sort
if 'date' not in df.columns:
    raise KeyError("'date' column is missing from the combined DataFrame.")
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by="date").reset_index(drop=True)

# 5. drop duplicates by address, date, zip_code
required_dedup_cols = ["address", "date", "zip_code"]
missing_dedup_cols = [col for col in required_dedup_cols if col not in df.columns]
if missing_dedup_cols:
    raise KeyError(f"Missing columns required for deduplication: {missing_dedup_cols}. Available columns: {df.columns.tolist()}")

df = df.drop_duplicates(subset=required_dedup_cols, keep="first").reset_index(drop=True)
print(f"Shape after deduplication: {df.shape}")

# 6. Select relevant columns for the model
relevant_cols = ['zip_code', 'date', 'purchase_price', 'city', 'sqm', 'no_rooms',
                 'year_build', 'sqm_price', 'area', 'region', 'house_type']
missing_relevant_cols = [col for col in relevant_cols if col not in df.columns]
if missing_relevant_cols:
    raise KeyError(f"Missing relevant columns for modeling: {missing_relevant_cols}. Available columns: {df.columns.tolist()}")
df_selected = df[relevant_cols].copy()

# 7. Subsample the last N rows for modeling
N_SUBSAMPLE = 200_000 # Keeping this for consistency with your original script
if len(df_selected) < N_SUBSAMPLE:
    print(f"Warning: DataFrame has only {len(df_selected)} rows after selection and deduplication. Using all available {len(df_selected)} rows for subsample.")
    sub = df_selected.copy()
else:
    sub = df_selected.iloc[-N_SUBSAMPLE:].copy()
print(f"Subsample shape: {sub.shape}")

sub['date_sequential_num'] = np.arange(len(sub))

# 8. Prepare X, y
cols_to_drop_for_X = ['date', 'purchase_price']
additional_datetime_cols_to_drop = []
for col in sub.columns:
    if col not in cols_to_drop_for_X and (pd.api.types.is_datetime64_any_dtype(sub[col]) or pd.api.types.is_period_dtype(sub[col])):
        additional_datetime_cols_to_drop.append(col)
cols_to_drop_for_X.extend(additional_datetime_cols_to_drop)
cols_to_drop_for_X = list(set(cols_to_drop_for_X))
print(f"Columns to drop for X: {cols_to_drop_for_X}")

X = pd.get_dummies(sub.drop(columns=cols_to_drop_for_X), drop_first=True)
y = sub['purchase_price'].to_numpy()

print(f"Shape of X before scaling: {X.shape}")
print(f"Number of features in X: {X.shape[1]}")

# 9. TimeSeriesSplit CV and model comparison
tscv = TimeSeriesSplit(n_splits=10, test_size=2000)

split_matrix_viz = np.zeros((tscv.get_n_splits(), len(X)))
for i, (train_idx_viz, test_idx_viz) in enumerate(tscv.split(X)):
    split_matrix_viz[i, train_idx_viz] = 1
    split_matrix_viz[i, test_idx_viz] = 2
plt.figure(figsize=(10, 3 * tscv.get_n_splits() / 5))
plt.imshow(split_matrix_viz, aspect='auto', cmap=plt.cm.coolwarm, interpolation='nearest')
plt.xlabel("Sample index")
plt.ylabel("CV split")
plt.title("TimeSeriesSplit train/test indices")
plt.colorbar(label='0=unused, 1=train, 2=test', ticks=[0,1,2])
plt.tight_layout()
plt.show()

# Define a base temporary directory for auto-sklearn runs
autosklearn_base_temp_dir = Path("./autosklearn_temp_working_dir")
autosklearn_base_temp_dir.mkdir(parents=True, exist_ok=True)

# --- auto-sklearn specific parameters ---
# These are short for demonstration. Increase for actual use.
time_for_task = 60  # Total time in seconds for auto-sklearn to run per CV split
per_run_time = 15   # Time limit in seconds for each model auto-sklearn tries

models = {
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "AutoSklearn": "placeholder" # Placeholder, will be instantiated in the loop
}

mae_scores_dict = {name: [] for name in models}

print("\n--- Training and evaluating splits ---")
split_num_print = 1
for train_idx, test_idx in tscv.split(X):
    X_train_raw, X_test_raw = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    print(f"\n--- Split {split_num_print}/{tscv.get_n_splits()} ---")
    print(f"Train size: {len(X_train_scaled)}, Test size: {len(X_test_scaled)}")

    for name, mdl_config in models.items():
        current_model = None
        if name == "AutoSklearn":
            # Create a unique temp folder for this specific auto-sklearn run
            # This ensures multiple auto-sklearn runs (e.g. in a loop or parallel) don't conflict
            # and that cleanup is more robust.
            # The folder name includes the split number to ensure uniqueness.
            temp_folder_for_split = autosklearn_base_temp_dir / f"split_{split_num_print}"
            # Clean up the specific temp folder from previous runs if it exists
            if temp_folder_for_split.exists():
                shutil.rmtree(temp_folder_for_split)
            temp_folder_for_split.mkdir(parents=True, exist_ok=True)

            current_model = autosklearn.regression.AutoSklearnRegressor(
                time_left_for_this_task=time_for_task,
                per_run_time_limit=per_run_time,
                n_jobs=-1,
                metric=autosklearn.metrics.mean_absolute_error, # Optimize for MAE
                # memory_limit=... # Optional: set memory limit in MB
                tmp_folder=str(temp_folder_for_split), # crucial for CV
                delete_tmp_folder_after_terminate=True # auto-sklearn will clean this specific folder
            )
        else:
            current_model = mdl_config # This is the RandomForestRegressor instance

        try:
            current_model.fit(X_train_scaled, y_train)
            # For auto-sklearn, you might want to see the chosen model:
            if name == "AutoSklearn":
                 # print(f"  AutoSklearn selected models: {current_model.show_models()}") # Very verbose
                 # print(f"  AutoSklearn ensemble performance: {current_model.sprint_statistics()}") # Statistics
                 pass


            y_pred = current_model.predict(X_test_scaled)

            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)

            mae_scores_dict[name].append(mae)

            print(f"  {name:15s} MAE: {mae:.0f}, RMSE: {rmse:.0f}")

            # Optional: If AutoSklearn was used, explicitly clean its specific temp folder
            # if name == "AutoSklearn" and temp_folder_for_split.exists():
            #     shutil.rmtree(temp_folder_for_split)
            # Note: delete_tmp_folder_after_terminate=True should handle this.

        except Exception as e:
            print(f"  Error training/predicting with {name} in split {split_num_print}: {e}")
            import traceback
            traceback.print_exc()
            mae_scores_dict[name].append(np.nan)
            # If error occurred with AutoSklearn, ensure its temp folder is cleaned if not done by auto-sklearn
            # if name == "AutoSklearn" and temp_folder_for_split.exists():
            #    shutil.rmtree(temp_folder_for_split)


    split_num_print += 1

# Clean up the base temporary directory after all splits if it's empty or only contains empty split folders
try:
    if autosklearn_base_temp_dir.exists():
        # Basic cleanup: remove if empty. More robust cleanup might be needed
        # if auto-sklearn fails to delete its subfolders.
        if not any(autosklearn_base_temp_dir.iterdir()):
             shutil.rmtree(autosklearn_base_temp_dir)
        else: # If it's not empty, it means some temp folders were not cleaned.
            print(f"Warning: Auto-sklearn base temp directory {autosklearn_base_temp_dir} is not empty after run.")
            # For a more aggressive cleanup: shutil.rmtree(autosklearn_base_temp_dir)
            # But be cautious with this, ensure no important data is there.
except Exception as e:
    print(f"Error during cleanup of auto-sklearn base temp directory: {e}")


print("\n--- Aggregated MAE Scores ---")
for name, scores in mae_scores_dict.items():
    if scores:
        valid_scores = [s for s in scores if not np.isnan(s)]
        if valid_scores:
            print(f"{name:15s} Mean MAE: {np.mean(valid_scores):.0f} ± {np.std(valid_scores):.0f} (from {len(valid_scores)} successful splits)")
        else:
            print(f"{name:15s} No successful splits to aggregate MAE.")
    else:
        print(f"{name:15s} No scores recorded.")

print("\n--- Script Finished ---")