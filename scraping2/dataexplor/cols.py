import pandas as pd
import time
import os
import math

def count_csv_rows(filepath):
    """Efficiently counts the number of rows in a CSV file."""
    print(f"   Counting rows in {os.path.basename(filepath)}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for row in f) - 1
    except Exception:
        return None

def preprocess_bbr_files(data_folder, output_folder):
    """
    Reads large BBR CSV files in chunks, selects only necessary columns,
    and saves them as smaller, efficient CSV files. Skips if already processed.
    """
    print("--- Step 1: Pre-processing large BBR files into smaller, efficient files ---")
    
    files_to_process = {
        'Enhed.csv': {
            'usecols': [
                'id_lokalId', 'bygning', 'status', 'virkningFra', 'virkningTil',
                'enh020EnhedensAnvendelse', 'enh023Boligtype', 'enh026EnhedensSamledeAreal', 
                'enh027ArealTilBeboelse', 'enh031AntalVærelser', 'enh065AntalVandskylledeToiletter', 
                'enh033Badeforhold', 'enh034Køkkenforhold', 'etage'
            ],
            'dtype': {'id_lokalId': 'str', 'bygning': 'str', 'enh023Boligtype': 'str'}
        },
        'Ejendomsrelation.csv': {
            'usecols': ['bfeNummer', 'ejerlejlighed', 'kommunekode', 'status', 'tinglystAreal', 'husnummer'],
            'dtype': {'ejerlejlighed': 'str', 'bfeNummer': 'float', 'husnummer': 'str'}
        },
        'EnhedEjendomsrelation.csv': {
            'usecols': ['enhed', 'ejerlejlighed', 'status'],
            'dtype': {'enhed': 'str', 'ejerlejlighed': 'str'}
        },
        'Bygning.csv': {
            'usecols': ['id_lokalId', 'byg026Opførelsesår', 'husnummer', 'byg038SamletBygningsareal'],
            'dtype': {'id_lokalId': 'str', 'husnummer': 'str'}
        }
    }

    for filename, config in files_to_process.items():
        input_path = os.path.join(data_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.csv', '_trimmed.csv'))
        
        print(f"\n--> Checking for '{filename}'...")
        if os.path.exists(output_path):
            print(f"    ✅ Found existing processed file at '{output_path}'. Skipping.")
            continue

        print(f"    -> No processed file found. Starting processing for '{filename}'...")
        try:
            chunk_size = 1500_000
            total_rows = count_csv_rows(input_path)
            total_chunks = math.ceil(total_rows / chunk_size) if total_rows is not None else 'N/A'
            print(f"    Total rows: {total_rows}, Total chunks: {total_chunks}")

            reader = pd.read_csv(input_path, usecols=config['usecols'], dtype=config['dtype'], chunksize=chunk_size, low_memory=False)
            
            header_written = False
            for i, chunk in enumerate(reader, 1):
                print(f"    -> Processing chunk {i}/{total_chunks}...")
                if not header_written:
                    chunk.to_csv(output_path, index=False, mode='w', header=True)
                    header_written = True
                else:
                    chunk.to_csv(output_path, index=False, mode='a', header=False)
            
            if header_written:
                print(f"    ✅ Saved trimmed data to '{output_path}'")
        except (FileNotFoundError, ValueError) as e:
            print(f"    ❌ ERROR processing '{filename}': {e}")

def enrich_from_processed_files(raw_data_folder, processed_folder, sales_file, final_output_path):
    """
    Loads pre-processed files and enriches sales data for all property types.
    """
    print("\n--- Step 2: Loading pre-processed data and enriching sales ---")
    try:
        # Load all necessary files
        sales_df = pd.read_csv(os.path.join(raw_data_folder, sales_file))
        sales_df['dato'] = pd.to_datetime(sales_df['dato'], errors='coerce', utc=True)
        sales_df.dropna(subset=['dato', 'bfe_nummer'], inplace=True)

        enhed_df = pd.read_csv(f"{processed_folder}/Enhed_trimmed.csv", low_memory=False)
        ej_rel_df = pd.read_csv(f"{processed_folder}/Ejendomsrelation_trimmed.csv", low_memory=False)
        enhed_ej_rel_df = pd.read_csv(f"{processed_folder}/EnhedEjendomsrelation_trimmed.csv", low_memory=False)
        byg_df = pd.read_csv(f"{processed_folder}/Bygning_trimmed.csv", low_memory=False)
        print("-> All necessary files loaded successfully.")

        # --- Build Lookup Tables ---
        ej_rel_gældende = ej_rel_df[ej_rel_df['status'] == 'gældende']
        enhed_ej_rel_gældende = enhed_ej_rel_df[enhed_ej_rel_df['status'] == 'gældende']
        
        # 1. Apartments: bfeNummer -> ejerlejlighed -> enhed
        apartments_map = pd.merge(ej_rel_gældende, enhed_ej_rel_gældende, on='ejerlejlighed').drop_duplicates(subset=['bfeNummer'])
        bfe_to_enhed_lookup = apartments_map.set_index('bfeNummer')['enhed'].to_dict()
        
        # 2. Villas: bfeNummer -> husnummer -> bygning
        non_apartments_df = ej_rel_gældende[ej_rel_gældende['ejerlejlighed'].isnull()].copy()
        villa_map = pd.merge(non_apartments_df, byg_df, on='husnummer').drop_duplicates(subset=['bfeNummer'])
        bfe_to_building_lookup = villa_map.set_index('bfeNummer')['id_lokalId'].to_dict()

        # 3. General Lookups
        bfe_to_komkode_lookup = pd.concat([apartments_map.set_index('bfeNummer')['kommunekode'], villa_map.set_index('bfeNummer')['kommunekode']]).to_dict()
        bfe_to_grundareal_lookup = pd.concat([apartments_map.set_index('bfeNummer')['tinglystAreal'], villa_map.set_index('bfeNummer')['tinglystAreal']]).to_dict()
        bygning_lookups = byg_df.set_index('id_lokalId')[['byg026Opførelsesår', 'byg038SamletBygningsareal']].to_dict('index')
        print("-> All lookup tables built successfully.")
        
        # --- Prepare Sales Data ---
        sales_df['enhed_id'] = sales_df['bfe_nummer'].map(bfe_to_enhed_lookup)
        sales_df['bygning_id'] = sales_df['bfe_nummer'].map(bfe_to_building_lookup)
        sales_df['kommunekode'] = sales_df['bfe_nummer'].map(bfe_to_komkode_lookup)
        sales_df['grund_areal'] = sales_df['bfe_nummer'].map(bfe_to_grundareal_lookup)

        apartments_sales = sales_df[sales_df['enhed_id'].notna()].copy()
        villa_sales = sales_df[sales_df['bygning_id'].notna()].copy()

        # --- Enrich Data in Chunks ---
        enhed_df['virkningFra'] = pd.to_datetime(enhed_df['virkningFra'], errors='coerce', utc=True)
        enhed_df['virkningTil'] = pd.to_datetime(enhed_df['virkningTil'], errors='coerce', utc=True)
        
        # Enrich Apartments
        enriched_apartments = pd.merge(apartments_sales, enhed_df, left_on='enhed_id', right_on='id_lokalId', how='inner')
        enriched_apartments = enriched_apartments.query("virkningFra <= dato and (dato < virkningTil or virkningTil.isnull())").copy()
        
        # Enrich Villas by Aggregating Units
        residential_units = enhed_df[enhed_df['enh020EnhedensAnvendelse'].isin([120, 130, 140])].copy()
        agg_rules = {
            'enh027ArealTilBeboelse': 'sum', 'enh031AntalVærelser': 'sum',
            'enh065AntalVandskylledeToiletter': 'sum', 'enh023Boligtype': 'first',
            'enh033Badeforhold': 'first', 'enh034Køkkenforhold': 'first'
        }
        building_summary = residential_units.groupby('bygning').agg(agg_rules).reset_index()
        enriched_villas = pd.merge(villa_sales, building_summary, left_on='bygning_id', right_on='bygning', how='inner')

        # Combine and Finalize
        final_df = pd.concat([enriched_apartments, enriched_villas], ignore_index=True).drop_duplicates(subset=['bfe_nummer', 'dato'])
        final_df['construction_year'] = final_df['bygning'].map({k: v['byg026Opførelsesår'] for k, v in bygning_lookups.items()})
        final_df['building_area'] = final_df['bygning'].map({k: v['byg038SamletBygningsareal'] for k, v in bygning_lookups.items()})

        # Rename and select final columns
        final_columns = {
            'bfe_nummer': 'bfe_nummer', 'kontant_koebesum': 'kontant_koebesum', 'samlet_koebesum': 'samlet_koebesum',
            'loesoeresum': 'loesoeresum', 'salgstype': 'salgstype', 'dato': 'dato', 'kommunekode': 'kommunekode',
            'grund_areal': 'grund_areal', 'enh023Boligtype': 'hustype', 'enh027ArealTilBeboelse': 'livable_area_at_sale',
            'enh031AntalVærelser': 'rooms_at_sale', 'enh065AntalVandskylledeToiletter': 'toilets_at_sale',
            'enh033Badeforhold': 'badeforhold', 'enh034Køkkenforhold': 'koekkenforhold', 'etage': 'etage',
            'construction_year': 'construction_year', 'building_area': 'building_area'
        }
        final_df_cols = [col for col in final_columns.keys() if col in final_df.columns]
        final_df = final_df[final_df_cols].rename(columns=final_columns)
        
        print(f"-> Successfully enriched {len(final_df)} records.")
        final_df.to_csv(final_output_path, index=False, encoding='utf-8')
        print(f"\n✅ Done. Final dataset saved to '{final_output_path}'")

    except Exception as e:
        print(f"❌ An error occurred during the enrichment phase: {e}")

if __name__ == "__main__":
    RAW_DATA_FOLDER = './'
    PROCESSED_DATA_FOLDER = os.path.join(RAW_DATA_FOLDER, 'processed')
    SALES_FILE = 'filtered_sales.csv'
    FINAL_CSV_PATH = os.path.join(RAW_DATA_FOLDER, 'final_enriched_sales_data.csv')

    start_time = time.time()
    
    os.makedirs(PROCESSED_DATA_FOLDER, exist_ok=True)

    preprocess_bbr_files(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER)
    
    enrich_from_processed_files(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER, SALES_FILE, FINAL_CSV_PATH)

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")