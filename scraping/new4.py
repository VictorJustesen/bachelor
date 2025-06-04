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

data_dir = Path(__file__).resolve().parent / "Housing_data_cleaned" # Adjusted path example
parquet_files = sorted(data_dir.glob("DKHousingprices_*.parquet"))

if not parquet_files:
    raise FileNotFoundError(f"No Parquet files found in {data_dir}. Please check the path: {data_dir.resolve()}")

# 2. read each into a DataFrame
df_list = [pd.read_parquet(p, engine="pyarrow") for p in parquet_files]

# 3. concatenate into one DataFrame
df = pd.concat(df_list, ignore_index=True)

print(df.isna().any())
print(df.shape)
df=df.dropna()

print(df.isna().any())
print(df.shape)