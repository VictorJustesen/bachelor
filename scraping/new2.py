# Filename: model_per_region.py

import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
# from xgboost import XGBRegressor # Uncomment if you plan to add XGBoost
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
# import matplotlib.pyplot as plt # Uncomment if you want to add per-area split visualizations

def run_regional_modeling():
    # 1. Locate all cleaned Parquet files
    try:
        script_dir = Path(__file__).resolve().parent
        # Assuming 'Housing_data_cleaned' is in the same directory as the script:
        data_dir = script_dir / "Housing_data_cleaned"
        # If 'Housing_data_cleaned' is in the parent directory (e.g., 'bachelor/Housing_data_cleaned' 
        # and script is in 'bachelor/scraping/'):
        # data_dir = script_dir.parent / "Housing_data_cleaned" 
        print(f"Attempting to read data from: {data_dir.resolve()}")
    except NameError: # Fallback for interactive environments like Jupyter
        # Adjust this relative path based on your notebook's CWD
        data_dir = Path(".").resolve() / "Housing_data_cleaned" 
        print(f"Warning: __file__ not defined. Using relative path for data_dir: {data_dir.resolve()}")

    parquet_files = sorted(data_dir.glob("DKHousingprices_*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(f"No Parquet files found in {data_dir}. Please check the path.")

    df_list = [pd.read_parquet(p, engine="pyarrow") for p in parquet_files]
    df = pd.concat(df_list, ignore_index=True)
    print(f"Initial total rows: {len(df)}")
    # print("Initial columns:", df.columns.tolist()) # Keep for debugging if needed

    if 'date' not in df.columns:
        raise KeyError("'date' column is missing from the combined DataFrame.")
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by="date").reset_index(drop=True)

    required_dedup_cols = ["address", "date", "zip_code"]
    missing_dedup_cols = [col for col in required_dedup_cols if col not in df.columns]
    if missing_dedup_cols:
        raise KeyError(f"Missing columns required for deduplication: {missing_dedup_cols}.")
    df = df.drop_duplicates(subset=required_dedup_cols, keep="first").reset_index(drop=True)
    print(f"Shape after deduplication: {df.shape}")

    SEGMENTATION_COLUMN = 'area' # Changed to 'area' as per your latest script

    relevant_cols = ['zip_code', 'date', 'purchase_price', 'city', 'sqm', 'no_rooms',
                     'year_build', SEGMENTATION_COLUMN, 'region', 'house_type']
    missing_relevant_cols = [col for col in relevant_cols if col not in df.columns]
    if missing_relevant_cols:
        raise KeyError(f"Missing relevant columns for modeling: {missing_relevant_cols}.")
    if SEGMENTATION_COLUMN not in df.columns:
        raise KeyError(f"The specified SEGMENTATION_COLUMN '{SEGMENTATION_COLUMN}' not found in DataFrame.")

    df_selected = df[relevant_cols].copy()
    df_selected=df_selected.dropna()

    N_OVERALL_SUBSAMPLE = 200_000
    if len(df_selected) > N_OVERALL_SUBSAMPLE:
        df_for_segment_modeling = df_selected.iloc[-N_OVERALL_SUBSAMPLE:].copy()
        print(f"Using last {len(df_for_segment_modeling)} rows overall for segmented modeling.")
    else:
        df_for_segment_modeling = df_selected.copy()
        print(f"Using all {len(df_for_segment_modeling)} available rows for segmented modeling (subsample size not met).")

    models_to_run = {
        # "LinearRegression": LinearRegression(), # Uncomment to include
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        # "XGBoost": XGBRegressor(objective="reg:squarederror", n_estimators=50, random_state=42, n_jobs=-1)
    }

    overall_results_storage = []

    unique_segments = df_for_segment_modeling[SEGMENTATION_COLUMN].unique()
    print(f"\nFound unique values in '{SEGMENTATION_COLUMN}': {unique_segments}")

    for segment_value in unique_segments:
        print(f"\n--- Processing {SEGMENTATION_COLUMN}: {segment_value} ---")
        segment_df = df_for_segment_modeling[df_for_segment_modeling[SEGMENTATION_COLUMN] == segment_value].copy()
        segment_df = segment_df.sort_values(by="date").reset_index(drop=True)

        MIN_SAMPLES_PER_SEGMENT_FOR_CV = 50 # Adjusted minimum, can be tuned
        if len(segment_df) < MIN_SAMPLES_PER_SEGMENT_FOR_CV:
            print(f"Skipping {SEGMENTATION_COLUMN} '{segment_value}' due to insufficient data: {len(segment_df)} rows (threshold: {MIN_SAMPLES_PER_SEGMENT_FOR_CV}).")
            continue
        
        segment_df['date_sequential_num'] = np.arange(len(segment_df))

        cols_to_drop_for_X_segment = ['date', 'purchase_price', SEGMENTATION_COLUMN]
        
        additional_datetime_cols_to_drop_segment = []
        for col in segment_df.columns:
            if col not in cols_to_drop_for_X_segment and \
               (pd.api.types.is_datetime64_any_dtype(segment_df[col]) or pd.api.types.is_period_dtype(segment_df[col])):
                additional_datetime_cols_to_drop_segment.append(col)
        
        current_cols_to_drop_segment = list(set(cols_to_drop_for_X_segment + additional_datetime_cols_to_drop_segment))

        X_segment_features_df = segment_df.drop(columns=current_cols_to_drop_segment, errors='ignore')
        y_segment = segment_df['purchase_price'].to_numpy()

        if X_segment_features_df.empty or X_segment_features_df.shape[1] == 0:
            print(f"No features remaining for {SEGMENTATION_COLUMN} '{segment_value}' after dropping columns. Skipping.")
            continue

        cat_cols_segment = X_segment_features_df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols_segment = X_segment_features_df.select_dtypes(include=[np.number]).columns.tolist()

        # print(f"{SEGMENTATION_COLUMN} '{segment_value}' - Features for X: {X_segment_features_df.columns.tolist()}") # Verbose
        print(f"{SEGMENTATION_COLUMN} '{segment_value}' - X_features_df shape: {X_segment_features_df.shape}, y_segment shape: {y_segment.shape}")

        preprocessor_segment = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), num_cols_segment),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse=True, drop=None), cat_cols_segment) 
            ],
            remainder='drop'
        )
        
        # TimeSeriesSplit settings per segment based on your requirements
        N_DATAPOINTS_SEGMENT = len(X_segment_features_df)
        TARGET_N_SPLITS = 10
        TARGET_TOTAL_TEST_FRACTION = 0.10
        MIN_SAMPLES_PER_TEST_SPLIT = 10  # Ensure test splits are not trivially small

        # Calculate ideal test size per split to achieve ~10% total test data with TARGET_N_SPLITS
        ideal_test_size_per_split = int(np.ceil((TARGET_TOTAL_TEST_FRACTION * N_DATAPOINTS_SEGMENT) / TARGET_N_SPLITS))
        actual_test_size_per_split = max(MIN_SAMPLES_PER_TEST_SPLIT, ideal_test_size_per_split)
        
        # Minimum initial training size (e.g., at least as large as one test split, or twice)
        min_initial_train_size = actual_test_size_per_split * 2 

        actual_n_splits_for_segment = 0
        if N_DATAPOINTS_SEGMENT >= min_initial_train_size + actual_test_size_per_split: # Check if at least one split is possible
            max_possible_splits = (N_DATAPOINTS_SEGMENT - min_initial_train_size) // actual_test_size_per_split
            actual_n_splits_for_segment = min(TARGET_N_SPLITS, max(1, max_possible_splits))
        
        if actual_n_splits_for_segment == 0:
            print(f"Skipping {SEGMENTATION_COLUMN} '{segment_value}': Calculated 0 CV splits possible with test_size={actual_test_size_per_split} and initial_train_size={min_initial_train_size} for {N_DATAPOINTS_SEGMENT} samples.")
            continue

        print(f"{SEGMENTATION_COLUMN} '{segment_value}' - Using TimeSeriesSplit with n_splits={actual_n_splits_for_segment}, test_size={actual_test_size_per_split}")
        tscv_segment = TimeSeriesSplit(n_splits=actual_n_splits_for_segment, test_size=actual_test_size_per_split)

        for model_name, model_instance_orig in models_to_run.items():
            if model_name == "LinearRegression": model_instance = LinearRegression()
            elif model_name == "RandomForest": model_instance = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            else: model_instance = model_instance_orig 

            pipeline_segment = Pipeline(steps=[('preprocessor', preprocessor_segment),
                                              ('regressor', model_instance)])
            
            segment_split_maes = []
            segment_split_rmses = []
            segment_total_test_samples_model = 0
            
            for split_i, (train_idx, test_idx) in enumerate(tscv_segment.split(X_segment_features_df)):
                if not train_idx.size > 0 or not test_idx.size > 0 :
                    print(f"  Skipping empty split {split_i+1} for {model_name} in {SEGMENTATION_COLUMN} '{segment_value}'")
                    continue

                X_train, X_test = X_segment_features_df.iloc[train_idx], X_segment_features_df.iloc[test_idx]
                y_train, y_test = y_segment[train_idx], y_segment[test_idx]
                
                try:
                    pipeline_segment.fit(X_train, y_train)
                    y_pred = pipeline_segment.predict(X_test)
                    
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    mae = mean_absolute_error(y_test, y_pred)
                    
                    segment_split_maes.append(mae)
                    segment_split_rmses.append(rmse)
                    segment_total_test_samples_model += len(y_test)
                except Exception as e:
                    print(f"  Error in Split {split_i+1} for {model_name} in {SEGMENTATION_COLUMN} '{segment_value}': {e}")
            
            if segment_split_maes:
                mean_mae_segment = np.mean(segment_split_maes)
                mean_rmse_segment = np.mean(segment_split_rmses)
                print(f"  {model_name:15s} | Mean MAE: {mean_mae_segment:.0f} | Mean RMSE: {mean_rmse_segment:.0f} (Splits: {len(segment_split_maes)}, Total Test Samples this model/segment: {segment_total_test_samples_model})")
                overall_results_storage.append({
                    SEGMENTATION_COLUMN: segment_value,
                    'model': model_name,
                    'mean_mae': mean_mae_segment,
                    'mean_rmse': mean_rmse_segment,
                    'total_test_samples': segment_total_test_samples_model, # This is total samples tested for this model in this area across all its splits
                    'num_cv_splits_conducted': len(segment_split_maes),
                    'n_datapoints_in_segment': N_DATAPOINTS_SEGMENT # Store total segment size for potential later inspection
                })
            else:
                print(f"  {model_name:15s} | No successful CV splits in {SEGMENTATION_COLUMN} '{segment_value}'.")

    results_df = pd.DataFrame(overall_results_storage)
    if not results_df.empty:
        print(f"\n\n--- Overall Model Performance (Weighted by Total Test Samples per {SEGMENTATION_COLUMN}) ---")
        for model_name in models_to_run.keys():
            model_results = results_df[results_df['model'] == model_name]
            if not model_results.empty and model_results['total_test_samples'].sum() > 0:
                weighted_avg_mae = np.average(model_results['mean_mae'], weights=model_results['total_test_samples'])
                weighted_avg_rmse = np.average(model_results['mean_rmse'], weights=model_results['total_test_samples'])
                print(f"\nModel: {model_name}")
                print(f"  Weighted Average MAE across {SEGMENTATION_COLUMN}s: {weighted_avg_mae:.0f}")
                print(f"  Weighted Average RMSE across {SEGMENTATION_COLUMN}s: {weighted_avg_rmse:.0f}")
                print(f"  Results per {SEGMENTATION_COLUMN} (sorted by MAE):")
                for _, row in model_results.sort_values(by='mean_mae').iterrows():
                    print(f"    {SEGMENTATION_COLUMN}: {str(row[SEGMENTATION_COLUMN]):<25}, MAE: {row['mean_mae']:<7.0f}, RMSE: {row['mean_rmse']:<7.0f}, Test Samples: {row['total_test_samples']:<7}, Splits: {row['num_cv_splits_conducted']}, Total in Seg: {row['n_datapoints_in_segment']}")
            else:
                print(f"\nModel: {model_name} - No results or test samples to calculate weighted average.")
    else:
        print(f"\nNo results recorded from any segment.")
        
    print("\n--- Script Finished ---")

run_regional_modeling()