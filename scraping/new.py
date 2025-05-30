import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

# 1. locate all cleaned Parquet files
data_dir = Path(__file__).parent / "Housing_data_cleaned"
parquet_files = sorted(data_dir.glob("DKHousingprices_*.parquet"))
# 2. read each into a DataFrame
df_list = [pd.read_parquet(p, engine="pyarrow") for p in parquet_files]

# 3. concatenate into one DataFrame
df = pd.concat(df_list, ignore_index=True)
print(df.columns)
# 4. convert date to datetime and sort
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by="date").reset_index(drop=True)

# 5. drop duplicates by address, date, zip_code
df = df.drop_duplicates(subset=["address", "date", "zip_code"], keep="first").reset_index(drop=True)
print(df.columns)
df = df[['zip_code', 'date', 'purchase_price', 'city', 'sqm', 'no_rooms', 'year_build', 'sqm_price', 'area', 'region', 'house_type']]

# 7. Subsample the last 200k rows for modeling
sub = df.iloc[-150_000:]

sub['date_num'] = sub['date'].astype('int64')  # nanoseconds since epoch
# Or, for days since epoch:
# sub['date_num'] = (sub['date'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D')

# 8. Prepare X, y (one-hot encode categoricals, scale numerics)
cols_to_drop = ['date', 'purchase_price']
for col in sub.columns:
    if pd.api.types.is_datetime64_any_dtype(sub[col]) or pd.api.types.is_period_dtype(sub[col]):
        cols_to_drop.append(col)


X = pd.get_dummies(sub.drop(columns=cols_to_drop), drop_first=True)
y = sub['purchase_price'].to_numpy()


scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("training")
# 9. TimeSeriesSplit CV and model comparison
tscv = TimeSeriesSplit(n_splits=10, test_size=3000)

split_num = 0
n_samples = len(X_scaled)
split_matrix = np.zeros((tscv.get_n_splits(), n_samples))

for split_num, (train_idx, test_idx) in enumerate(tscv.split(X_scaled)):
    split_matrix[split_num, train_idx] = 1  # Mark train indices
    split_matrix[split_num, test_idx] = 2  # Mark test indices
plt.figure(figsize=(10, 3))
plt.imshow(split_matrix, aspect='auto', cmap=plt.cm.coolwarm, interpolation='nearest')
plt.xlabel("Sample index")
plt.ylabel("CV split")
plt.title("TimeSeriesSplit train/test indices")
plt.colorbar(label='0=unused, 1=train, 2=test')
plt.tight_layout()
plt.show()

models = {
    #"LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=150, random_state=42),
    #"XGBoost": XGBRegressor(objective="reg:absoluteerror", n_estimators=50, random_state=42)
}

# Initialize a dictionary to store RMSEs for each model
rmse_scores = {name: [] for name in models}

print("training and evaluating splits")
split_num = 1
for train_idx, test_idx in tscv.split(X_scaled):
    X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    for name, mdl in models.items():
        mdl.fit(X_train, y_train)
        y_pred = mdl.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        rmse_scores[name].append(mae)
        print(f"Split {split_num} | {name:15s} MAE: {mae:.0f} (test size: {len(y_test)})")
    split_num += 1

# Print aggregated scores
print("\nAggregated MAE scores:")
for name, scores in rmse_scores.items():
    print(f"{name:15s} Mean MAE: {np.mean(scores):.0f} ± {np.std(scores):.0f}")

print("\n--- Script Finished ---")