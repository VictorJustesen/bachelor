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
import multiprocessing # Added for freeze_support

def run_modeling():
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
                     'year_build', 'area', 'region', 'house_type']
    missing_relevant_cols = [col for col in relevant_cols if col not in df.columns]
    if missing_relevant_cols:
        raise KeyError(f"Missing relevant columns for modeling: {missing_relevant_cols}. Available columns: {df.columns.tolist()}")
    df_selected = df[relevant_cols].copy()

    # 7. Subsample the last N rows for modeling
    N_SUBSAMPLE = 200_000 # As per your latest pasted code
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
    tscv = TimeSeriesSplit(n_splits=5, test_size=10000)

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
    autosklearn_base_temp_dir = Path("./autosklearn_temp_working_dir").resolve()
    autosklearn_base_temp_dir.mkdir(parents=True, exist_ok=True)

    # --- auto-sklearn specific parameters ---
    time_for_task =1800  # Total time in seconds for auto-sklearn per CV split (e.g., 5 minutes)
# For real runs, you might need much more, e.g., 3600 (1 hour) or more per split.
    per_run_time = 120
    
    models = {
        #"RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "AutoSklearn": "placeholder" 
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
            temp_folder_for_split = None # Initialize for robust error handling

            if name == "AutoSklearn":
                temp_folder_for_split = autosklearn_base_temp_dir / f"split_{split_num_print}"
                    # Clean up the specific temp folder if it exists from a PREVIOUS SCRIPT RUN
                if temp_folder_for_split.exists():
                    shutil.rmtree(temp_folder_for_split)
                
                # Let auto-sklearn create the temp_folder_for_split directory

                current_model = autosklearn.regression.AutoSklearnRegressor(
                    time_left_for_this_task=time_for_task,
                    per_run_time_limit=per_run_time,
                    n_jobs=-1, # For full parallelism. If issues persist, try n_jobs=1 for diagnostics.
                    metric=autosklearn.metrics.mean_absolute_error,
                    memory_limit=7000,
                    # memory_limit=... # Optional: set memory limit in MB if needed on HPC
                    tmp_folder=str(temp_folder_for_split), 
                    delete_tmp_folder_after_terminate=True 
                )

                
            else:
                current_model = mdl_config

            try:
                current_model.fit(X_train_scaled, y_train)
                if name == "AutoSklearn":
                    print(f"  AutoSklearn selected models: {current_model.show_models()}")
                    print(f"  AutoSklearn ensemble performance: {current_model.sprint_statistics()}")
                    pass

                y_pred = current_model.predict(X_test_scaled)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                mae_scores_dict[name].append(mae)
                print(f"  {name:15s} MAE: {mae:.0f}, RMSE: {rmse:.0f}")

            except Exception as e:
                print(f"  Error training/predicting with {name} in split {split_num_print}: {e}")
                import traceback
                traceback.print_exc()
                mae_scores_dict[name].append(np.nan)
                # Robust cleanup attempt if auto-sklearn errored and temp_folder_for_split was defined
                if name == "AutoSklearn" and temp_folder_for_split and temp_folder_for_split.exists():
                    try:
                        shutil.rmtree(temp_folder_for_split)
                        print(f"    Cleaned up {temp_folder_for_split} after error.")
                    except Exception as cleanup_e:
                        print(f"    Error during cleanup of {temp_folder_for_split} after exception: {cleanup_e}")
        split_num_print += 1

    try:
        if autosklearn_base_temp_dir.exists():
            if not any(autosklearn_base_temp_dir.iterdir()):
                 shutil.rmtree(autosklearn_base_temp_dir)
            else:
                print(f"Warning: Auto-sklearn base temp directory {autosklearn_base_temp_dir} is not empty after run.")
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

if __name__ == '__main__':
    multiprocessing.freeze_support() # Call this early
    run_modeling()