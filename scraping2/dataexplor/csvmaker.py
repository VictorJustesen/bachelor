import pandas as pd
import json
import time

def analyze_and_convert(json_path, csv_path):
    """
    Loads the filtered sales data, analyzes it, and converts it to a CSV file.

    Args:
        json_path (str): The path to the input JSON file.
        csv_path (str): The path to save the output CSV file.
    """
    print(f"Loading data from '{json_path}'...")
    try:
        # Use pandas to easily read the JSON array into a DataFrame
        df = pd.read_json(json_path)
        print("Data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at '{json_path}'.")
        print("Please make sure you have run the previous trimming script.")
        return
    except ValueError as e:
        print(f"❌ ERROR: Could not parse the JSON file. It might be empty or malformed: {e}")
        return

    if df.empty:
        print("⚠️ The DataFrame is empty. No data to process.")
        return

    # --- Data Analysis ---
    print("\n--- Data Analysis Summary ---")
    num_sales = len(df)
    num_unique_bfes = df['bfe_nummer'].nunique()
    
    print(f"Total number of sales found: {num_sales}")
    print(f"Total number of unique properties (BFEs): {num_unique_bfes}")
    
    # --- Data Cleaning (Optional but Recommended) ---
    # Ensure 'dato' is a proper datetime format
    df['dato'] = pd.to_datetime(df['dato'], errors='coerce')
    # Drop rows where the date could not be parsed
    df.dropna(subset=['dato'], inplace=True)
    
    print(f"\nData range (by date): {df['dato'].min().date()} to {df['dato'].max().date()}")

    # --- CSV Conversion ---
    print(f"\nConverting data to CSV format at '{csv_path}'...")
    try:
        # index=False prevents pandas from writing row numbers into the CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print("✅ Successfully created CSV file.")
    except Exception as e:
        print(f"❌ ERROR: Could not save the CSV file. {e}")


if __name__ == "__main__":
    # The file created by the previous script
    INPUT_JSON_PATH = './filtered_with_both_prices.json'
    
    # The new CSV file we will create
    OUTPUT_CSV_PATH = './sales_data3.csv'

    start_time = time.time()
    
    analyze_and_convert(INPUT_JSON_PATH, OUTPUT_CSV_PATH)

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")