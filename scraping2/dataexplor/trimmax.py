import pandas as pd
import time

def load_sales_data(data_folder, sales_file):
    """Loads the initial sales data CSV."""
    print("Loading sales data...")
    try:
        sales_path = f"{data_folder}/{sales_file}"
        sales_df = pd.read_csv(sales_path)
        # The utc=True parameter is added to handle the timezone warning
        sales_df['dato'] = pd.to_datetime(sales_df['dato'], errors='coerce', utc=True)
        sales_df.dropna(subset=['dato', 'bfe_nummer'], inplace=True)
        print(f"-> Loaded {len(sales_df)} sales records from '{sales_file}'")
        return sales_df
    except FileNotFoundError:
        print(f"❌ ERROR: Sales data file not found: {sales_path}")
        return None

def build_lookup_tables(data_folder, ejendomsrelation_file, enhed_ejendomsrelation_file, bygning_file):
    """Builds lookup dictionaries from BBR files in a memory-efficient way."""
    print("Building lookup tables from BBR files...")
    try:
        # --- CORRECTED 2-STEP LINKING PROCESS ---

        # Step 1: Load both relation files
        ej_rel_path = f"{data_folder}/{ejendomsrelation_file}"
        ej_rel_df = pd.read_csv(
            ej_rel_path,
            usecols=['bfeNummer', 'ejerlejlighed', 'status'],
            dtype={'ejerlejlighed': 'str', 'bfeNummer': 'float'},
            low_memory=False
        )
        ej_rel_df = ej_rel_df[ej_rel_df['status'] == 'gældende']

        enhed_ej_rel_path = f"{data_folder}/{enhed_ejendomsrelation_file}"
        enhed_ej_rel_df = pd.read_csv(
            enhed_ej_rel_path,
            usecols=['enhed', 'ejerlejlighed', 'status'],
            dtype={'enhed': 'str', 'ejerlejlighed': 'str'},
            low_memory=False
        )
        enhed_ej_rel_df = enhed_ej_rel_df[enhed_ej_rel_df['status'] == 'gældende']

        # Step 2: Merge them on the common 'ejerlejlighed' key
        merged_relations = pd.merge(ej_rel_df, enhed_ej_rel_df, on='ejerlejlighed', how='inner')
        
        # Step 3: Create the final BFE -> Enhed lookup table
        merged_relations = merged_relations.drop_duplicates(subset=['bfeNummer'])
        bfe_to_enhed_lookup = merged_relations.set_index('bfeNummer')['enhed'].to_dict()
        print(f"-> Created BFE-to-Unit lookup table by joining two files.")

        # Build Bygning -> Construction Year lookup
        byg_path = f"{data_folder}/{bygning_file}"
        byg_df = pd.read_csv(
            byg_path,
            usecols=['id_lokalId', 'byg026Opførelsesår'],
            dtype={'id_lokalId': 'str'},
            low_memory=False
        )
        bygning_lookup = byg_df.set_index('id_lokalId')['byg026Opførelsesår'].to_dict()
        print(f"-> Created Building-to-Year lookup table.")

        return bfe_to_enhed_lookup, bygning_lookup
    except FileNotFoundError as e:
        print(f"❌ ERROR: A required BBR file was not found: {e}")
        return None, None
    except ValueError as e:
        print(f"❌ ERROR: A column was not found in a BBR file. {e}")
        print("Please check that the column names in the script match your CSV files exactly.")
        return None, None


def enrich_sales_data_chunked(sales_df, data_folder, enhed_file, bfe_to_enhed_lookup, bygning_lookup):
    """Processes the large Enhed.csv in chunks to enrich sales data."""
    print("\nStarting chunk-based enrichment process...")

    sales_df['enhed'] = sales_df['bfe_nummer'].map(bfe_to_enhed_lookup)
    
    sales_to_process = sales_df.dropna(subset=['enhed']).copy()
    print(f"-> Will process {len(sales_to_process)} sales with a valid BBR unit link.")

    enhed_path = f"{data_folder}/{enhed_file}"
    chunk_size = 1_000_000
    reader = pd.read_csv(
        enhed_path,
        chunksize=chunk_size,
        dtype={'id_lokalId': 'str', 'bygning': 'str'},
        low_memory=False
    )

    enriched_chunks = []
    chunk_num = 1
    
    for enhed_chunk in reader:
        print(f"--> Processing Enhed chunk {chunk_num}...")
        
        enhed_chunk['virkningFra'] = pd.to_datetime(enhed_chunk['virkningFra'], errors='coerce', utc=True)
        enhed_chunk['virkningTil'] = pd.to_datetime(enhed_chunk['virkningTil'], errors='coerce', utc=True)
        
        merged_chunk = pd.merge(sales_to_process, enhed_chunk, left_on='enhed', right_on='id_lokalId', how='inner')
        
        historical_matches = merged_chunk.query(
            "virkningFra <= dato and (dato < virkningTil or virkningTil.isnull())"
        ).copy()
        
        if not historical_matches.empty:
            enriched_chunks.append(historical_matches)
        
        chunk_num += 1

    if not enriched_chunks:
        print("⚠️ No historical matches found. The final file will be empty.")
        return pd.DataFrame()

    print("Combining all processed chunks...")
    final_df = pd.concat(enriched_chunks, ignore_index=True)

    final_df['construction_year'] = final_df['bygning'].map(bygning_lookup)

    final_columns = {
        'bfe_nummer': 'bfe_nummer',
        'kontant_koebesum': 'kontant_koebesum',
        'samlet_koebesum': 'samlet_koebesum',
        'loesoeresum': 'loesoeresum',
        'salgstype': 'salgstype',
        'dato': 'dato',
        'enh026EnhedensSamledeAreal': 'area_at_sale',
        'enh031AntalVærelser': 'rooms_at_sale',
        'enh065AntalVandskylledeToiletter': 'toilets_at_sale',
        'construction_year': 'construction_year'
    }
    final_df_cols = [col for col in final_columns.keys() if col in final_df.columns]
    final_df = final_df[final_df_cols].rename(columns=final_columns)
    
    return final_df

if __name__ == "__main__":
    DATA_FOLDER = './processed'
    SALES_FILE = 'sales_data3.parquet'
    BBR_ENHED_FILE = 'Enhed.parquet'
    BBR_EJENDOMSRELATION_FILE = 'Ejendomsrelation.parquet'
    BBR_ENHED_EJENDOMSRELATION_FILE = 'EnhedEjendomsrelation.parquet' # Added this file
    BBR_BYGNING_FILE = 'Bygning.parquet'
    FINAL_CSV_PATH = f'{DATA_FOLDER}/final_enriched_sales_data.csv'

    start_time = time.time()

    sales_df = load_sales_data(DATA_FOLDER, SALES_FILE)
    
    if sales_df is not None:
        bfe_to_enhed_lookup, bygning_lookup = build_lookup_tables(
            DATA_FOLDER, BBR_EJENDOMSRELATION_FILE, BBR_ENHED_EJENDOMSRELATION_FILE, BBR_BYGNING_FILE
        )
        
        if bfe_to_enhed_lookup is not None:
            enriched_df = enrich_sales_data_chunked(
                sales_df, DATA_FOLDER, BBR_ENHED_FILE, bfe_to_enhed_lookup, bygning_lookup
            )
            
            print(f"\nSaving final enriched data to '{FINAL_CSV_PATH}'...")
            enriched_df.to_csv(FINAL_CSV_PATH, index=False, encoding='utf-8')
            print("✅ Done.")

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")