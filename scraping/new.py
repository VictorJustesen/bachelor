import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

# 1. locate all cleaned Parquet files
# Assuming this script is in the 'scraping' directory, and 'Housing_data_cleaned'
# is in the parent 'bachelor' directory. Adjust if your structure is different.
# e.g., if 'Housing_data_cleaned' is in the same 'scraping' folder:
# data_dir = Path(__file__).resolve().parent / "Housing_data_cleaned"
data_dir = Path(__file__).resolve().parent / "Housing_data_cleaned" # Adjusted path example
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
# Check if all required columns for deduplication exist
missing_dedup_cols = [col for col in required_dedup_cols if col not in df.columns]
if missing_dedup_cols:
    raise KeyError(f"Missing columns required for deduplication: {missing_dedup_cols}. Available columns: {df.columns.tolist()}")

df = df.drop_duplicates(subset=required_dedup_cols, keep="first").reset_index(drop=True)
print(f"Shape after deduplication: {df.shape}")

# 6. Select relevant columns for the model (do this *before* subsampling to ensure columns exist)
relevant_cols = ['zip_code', 'date', 'purchase_price', 'city', 'sqm', 'no_rooms', 
                 'year_build', 'area', 'region', 'house_type']
# Check if all relevant columns exist
missing_relevant_cols = [col for col in relevant_cols if col not in df.columns]
if missing_relevant_cols:
    raise KeyError(f"Missing relevant columns for modeling: {missing_relevant_cols}. Available columns: {df.columns.tolist()}")
df_selected = df[relevant_cols].copy() # Use .copy() to avoid SettingWithCopyWarning later

# 7. Subsample the last N rows for modeling
N_SUBSAMPLE = 1000_000
if len(df_selected) < N_SUBSAMPLE:
    print(f"Warning: DataFrame has only {len(df_selected)} rows after selection and deduplication. Using all available {len(df_selected)} rows for subsample.")
    sub = df_selected.copy()
else:
    sub = df_selected.iloc[-N_SUBSAMPLE:].copy()
print(f"Subsample shape: {sub.shape}")

# Create a numerical date feature: 0 for the first row in the subsample, 1 for the next, etc.
sub['date_sequential_num'] = np.arange(len(sub))

# 8. Prepare X, y
# 'date' (original datetime) will be dropped.
# 'date_sequential_num' will be kept as a numerical feature if not explicitly dropped.
# 'purchase_price' is the target.
cols_to_drop_for_X = ['date', 'purchase_price'] # Original datetime 'date' is dropped

# Identify any other datetime/period columns that might have been missed and should be dropped
# This loop is generally fine, but ensure 'date_sequential_num' is not accidentally caught if it's not datetime
additional_datetime_cols_to_drop = []
for col in sub.columns:
    if col not in cols_to_drop_for_X and (pd.api.types.is_datetime64_any_dtype(sub[col]) or pd.api.types.is_period_dtype(sub[col])):
        additional_datetime_cols_to_drop.append(col)

cols_to_drop_for_X.extend(additional_datetime_cols_to_drop)
cols_to_drop_for_X = list(set(cols_to_drop_for_X)) # Ensure unique columns

print(f"Columns to drop for X: {cols_to_drop_for_X}")
print(df.shape)
sub=sub.dropna()
print(df.shape)
X = pd.get_dummies(sub.drop(columns=cols_to_drop_for_X), drop_first=True)
y = sub['purchase_price'].to_numpy()

print(f"Shape of X before scaling: {X.shape}")
print(f"Number of features in X: {X.shape[1]}") # This will show how many columns pd.get_dummies created

# 9. TimeSeriesSplit CV and model comparison
tscv = TimeSeriesSplit(n_splits=3, test_size=5000) # Using 10 splits as in your code

# Visualize the splits (using unscaled X or y is fine for index visualization)
split_matrix_viz = np.zeros((tscv.get_n_splits(), len(X)))
for i, (train_idx_viz, test_idx_viz) in enumerate(tscv.split(X)):
    split_matrix_viz[i, train_idx_viz] = 1
    split_matrix_viz[i, test_idx_viz] = 2
plt.figure(figsize=(10, 3 * tscv.get_n_splits() / 5)) # Adjust figure height based on splits
plt.imshow(split_matrix_viz, aspect='auto', cmap=plt.cm.coolwarm, interpolation='nearest')
plt.xlabel("Sample index")
plt.ylabel("CV split")
plt.title("TimeSeriesSplit train/test indices")
plt.colorbar(label='0=unused, 1=train, 2=test', ticks=[0,1,2])
plt.tight_layout()
plt.show()

models = {
    #"LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1), # n_jobs=-1 for parallelism
    #"XGBoost": XGBRegressor(objective="reg:squarederror", n_estimators=50, random_state=42, n_jobs=-1)
}

# Initialize a dictionary to store MAEs for each model
mae_scores_dict = {name: [] for name in models}

print("\n--- Training and evaluating splits ---")
split_num_print = 1
for train_idx, test_idx in tscv.split(X): # Split the unscaled X
    X_train_raw, X_test_raw = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Scale features *within* the CV split
    # Important: Fit scaler ONLY on training data, then transform both train and test
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    print(f"\n--- Split {split_num_print}/{tscv.get_n_splits()} ---")
    print(f"Train size: {len(X_train_scaled)}, Test size: {len(X_test_scaled)}")

    for name, mdl in models.items():
        try:
            mdl.fit(X_train_scaled, y_train)
            y_pred = mdl.predict(X_test_scaled)
            
            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            
            mae_scores_dict[name].append(mae) # Storing MAE as per previous print logic
            
            print(f"  {name:15s} MAE: {mae:.0f}, RMSE: {rmse:.0f}")
        except Exception as e:
            print(f"  Error training/predicting with {name} in split {split_num_print}: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            mae_scores_dict[name].append(np.nan) # Record NaN if model fails for this split

    split_num_print += 1

# Print aggregated scores
print("\n--- Aggregated MAE Scores ---")
for name, scores in mae_scores_dict.items():
    if scores: # Check if list is not empty
        valid_scores = [s for s in scores if not np.isnan(s)]
        if valid_scores:
            print(f"{name:15s} Mean MAE: {np.mean(valid_scores):.0f} ± {np.std(valid_scores):.0f} (from {len(valid_scores)} successful splits)")
        else:
            print(f"{name:15s} No successful splits to aggregate MAE.")
    else:
        print(f"{name:15s} No scores recorded.")
        
print("\n--- Script Finished ---")