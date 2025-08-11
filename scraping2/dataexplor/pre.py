import pandas as pd
import time
import os
import math

def count_csv_rows(filepath):
    """Efficiently counts the number of rows in a CSV file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Subtract 1 for the header row
            return sum(1 for row in f) - 1
    except Exception:
        # Fallback for potential encoding or read errors
        return None

def preprocess_bbr_files(data_folder, output_folder):
    """
    Reads large BBR CSV files in chunks, selects only necessary columns,
    and saves them as smaller, efficient Parquet files.
    """
    print("Starting BBR pre-processing in memory-efficient chunk mode...")
    
    files_to_process = {
        'Enhed.csv': {
            'usecols': [
                'id_lokalId', 'bygning', 'status', 'virkningFra', 'virkningTil',
                'enh026EnhedensSamledeAreal', 'enh031AntalVærelser', 
                'enh065AntalVandskylledeToiletter', 'enh023Boligtype', 
                'enh033Badeforhold', 'enh034Køkkenforhold', 'etage'
            ],
            'dtype': {'id_lokalId': 'str', 'bygning': 'str', 'enh023Boligtype': 'str'},
            'output_name': 'Enhed_trimmed.parquet'
        },
        'Ejendomsrelation.csv': {
            'usecols': ['bfeNummer', 'ejerlejlighed', 'kommunekode', 'status'],
            'dtype': {'ejerlejlighed': 'str', 'bfeNummer': 'float'},
            'output_name': 'Ejendomsrelation_trimmed.parquet'
        },
        'EnhedEjendomsrelation.csv': {
            'usecols': ['enhed', 'ejerlejlighed', 'status'],
            'dtype': {'enhed': 'str', 'ejerlejlighed': 'str'},
            'output_name': 'EnhedEjendomsrelation_trimmed.parquet'
        },
        'Bygning.csv': {
            'usecols': ['id_lokalId', 'byg026Opførelsesår'],
            'dtype': {'id_lokalId': 'str'},
            'output_name': 'Bygning_trimmed.parquet'
        }
    }

    for filename, config in files_to_process.items():
        input_path = os.path.join(data_folder, filename)
        output_path = os.path.join(output_folder, config['output_name'])
        
        print(f"\n--> Preparing to process '{filename}'...")
        try:
            chunk_size = 500_000
            processed_chunks = []
            
            # First, get the total number of rows to calculate chunks
            total_rows = count_csv_rows(input_path)
            if total_rows is None:
                print(f"    ⚠️ Could not determine total rows for '{filename}'. Proceeding without progress count.")
                total_chunks = 'N/A'
            else:
                total_chunks = math.ceil(total_rows / chunk_size)
                print(f"    Total rows: {total_rows}, Total chunks: {total_chunks}")

            reader = pd.read_csv(
                input_path,
                usecols=config['usecols'],
                dtype=config['dtype'],
                chunksize=chunk_size,
                low_memory=False
            )
            
            # Iterate over each chunk with a progress counter
            for i, chunk in enumerate(reader, 1):
                print(f"    -> Processing chunk {i}/{total_chunks}...")
                processed_chunks.append(chunk)
            
            if processed_chunks:
                final_df = pd.concat(processed_chunks, ignore_index=True)
                final_df.to_parquet(output_path)
                print(f"    ✅ Saved trimmed data to '{output_path}'")
            else:
                print(f"    ⚠️ No data found in '{filename}'.")

        except FileNotFoundError:
            print(f"    ❌ ERROR: File not found at '{input_path}'. Skipping.")
        except ValueError as e:
            print(f"    ❌ ERROR: Column mismatch in '{filename}'. {e}")
            print("        Please verify the 'usecols' in the script match your file.")

if __name__ == "__main__":
    RAW_DATA_FOLDER = './'
    PROCESSED_DATA_FOLDER = './processed'
    
    os.makedirs(PROCESSED_DATA_FOLDER, exist_ok=True)

    start_time = time.time()
    preprocess_bbr_files(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER)
    end_time = time.time()
    
    print(f"\nBBR pre-processing finished in {end_time - start_time:.2f} seconds.")