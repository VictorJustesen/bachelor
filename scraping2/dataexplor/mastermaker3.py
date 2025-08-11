import pandas as pd
import time
import os
import math

pd.options.display.max_columns = None


def preprocess_for_building_enrichment(data_folder, output_folder):
    """
    Forbehandler kun de CSV-filer, der er nødvendige for at forbinde et salg
    til en bygning, og sikrer at de nødvendige kolonner er med.
    """
    print("--- Stadie 1: Forbehandling af filer til bygningsberigelse ---")
    
    files_to_process = {
        'Ejendomsrelation.csv': {
            'usecols': [
                'id_lokalId', 'bfeNummer', 'status', 
                'tinglystAreal', 'virkningFra', 'virkningTil'
            ],
            'dtype': {'id_lokalId': 'str', 'tinglystAreal': 'float'}
        },
        'Bygning.csv': {
            'usecols': [
                'id_lokalId', 'byg021BygningensAnvendelse', 'byg026Opførelsesår', 
                'grund', 'byg038SamletBygningsareal', 'status', 
                'virkningFra', 'virkningTil'
            ],
            'dtype': {'id_lokalId': 'str', 'grund': 'str', 'byg021BygningensAnvendelse': 'str'}
        },
        'Grund.csv': {
            'usecols': ['id_lokalId', 'bestemtFastEjendom', 'status'],
            'dtype': {'id_lokalId': 'str', 'bestemtFastEjendom': 'str'}
        }
    }
    
    os.makedirs(output_folder, exist_ok=True)

    for filename, config in files_to_process.items():
        input_path = os.path.join(data_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.csv', '_trimmed.csv'))
        
        if os.path.exists(output_path):
            print(f"    -> Behandlet fil for '{filename}' eksisterer allerede. Springer over.")
            continue

        print(f"    -> Behandler '{filename}'...")
        try:
            # Læser hele filen, da forbehandling kun køres én gang
            df = pd.read_csv(input_path, usecols=config['usecols'], dtype=config.get('dtype', {}), low_memory=False)
            df.to_csv(output_path, index=False)
            print(f"    ✅ Gemte trimmede data til '{output_path}'")
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"    ❌ FEJL under behandling af '{filename}': {e}")


def enrich_with_building_data(raw_data_folder, processed_folder, sales_file, final_output_path):
    """
    Kombinerer salgsdata med BBR for at finde det summerede areal af alle relevante
    bygninger på en ejendom på salgstidspunktet, ved brug af chunking.
    """
    print("\n--- Stadie 2: Sammensætning af pris og summeret bygningsareal ---")
    
    try:
        # --- Trin 1: Indlæs indledende filer ---
        print("    -> Indlæser salgs-, ejendoms- og grunddata...")
        sales_df = pd.read_csv(os.path.join(raw_data_folder, sales_file), low_memory=False)
        ej_rel_df = pd.read_csv(os.path.join(processed_folder, 'Ejendomsrelation_trimmed.csv'), dtype=str, low_memory=False)
        grund_df = pd.read_csv(os.path.join(processed_folder, 'Grund_trimmed.csv'), dtype=str, low_memory=False)

        # --- Trin 2: Forbered og rens indledende data ---
        print("    -> Forbereder data og konverterer datotyper...")
        sales_df.rename(columns={'bfe_nummer': 'bfeNummer'}, inplace=True)
        sales_df['dato'] = pd.to_datetime(sales_df['dato'], errors='coerce', utc=True)
        ej_rel_df['virkningFra'] = pd.to_datetime(ej_rel_df['virkningFra'], errors='coerce', utc=True)
        ej_rel_df['virkningTil'] = pd.to_datetime(ej_rel_df['virkningTil'], errors='coerce', utc=True)
        
        sales_df['bfeNummer'] = pd.to_numeric(sales_df['bfeNummer'], errors='coerce')
        ej_rel_df['bfeNummer'] = pd.to_numeric(ej_rel_df['bfeNummer'], errors='coerce')
        
        sales_df.dropna(subset=['bfeNummer', 'dato'], inplace=True)
        ej_rel_df.dropna(subset=['bfeNummer', 'virkningFra', 'id_lokalId'], inplace=True)
        grund_df.dropna(subset=['bestemtFastEjendom', 'id_lokalId'], inplace=True)

        # --- Trin 3: Byg den indledende kæde: Salg -> Ejendom -> Grund ---
        print("    -> Bygger den indledende datakæde: Salg -> Ejendom -> Grund...")
        merged_df = pd.merge(sales_df, ej_rel_df, on='bfeNummer', how='inner')
        query_ej = "virkningFra <= dato and (dato < virkningTil or virkningTil.isnull())"
        valid_ej = merged_df.query(query_ej)
        
        sales_ready_for_building = pd.merge(valid_ej, grund_df, left_on='id_lokalId', right_on='bestemtFastEjendom', how='inner')
        print(f"       - {len(sales_ready_for_building)} salg klar til at blive beriget med bygningsdata.")

        # --- Trin 4: Iterer gennem bygningsdata i bidder ---
        print("    -> Behandler bygningsdata i bidder...")
        bygning_reader = pd.read_csv(os.path.join(processed_folder, 'Bygning_trimmed.csv'), chunksize=500_000, low_memory=False, dtype=str)
        enriched_chunks = []

        residential_codes = [str(float(code)) for code in range(110, 191)] + ['510.0']

        for i, bygning_chunk in enumerate(bygning_reader, 1):
            print(f"       - Behandler bygnings-bid {i}...")
            if i == 1:
                print(bygning_chunk.head(10))  # Vis de første 3 rækker af den første bid for at kontrollere indlæsning
                print(sales_ready_for_building.head(10))  # Vis de første 3 rækker af salgsdata for at kontrollere indlæsning
            bygning_chunk['virkningFra'] = pd.to_datetime(bygning_chunk['virkningFra'], errors='coerce', utc=True)
            bygning_chunk['virkningTil'] = pd.to_datetime(bygning_chunk['virkningTil'], errors='coerce', utc=True)
            bygning_chunk.dropna(subset=['grund', 'virkningFra', 'byg038SamletBygningsareal'], inplace=True)
            if i == 1:
                print(f"{bygning_chunk.head(10)}")
            bygning_chunk = bygning_chunk[bygning_chunk['byg021BygningensAnvendelse'].isin(residential_codes)]
            if i == 1:
                print(f"{bygning_chunk.head(10)}")
            merged_chunk = pd.merge(sales_ready_for_building, bygning_chunk, left_on='id_lokalId_y', right_on='grund', how='inner')

            query_byg = "virkningFra_y <= dato and (dato < virkningTil_y or virkningTil_y.isnull())"
            valid_chunk = merged_chunk.query(query_byg)
            
            if not valid_chunk.empty:
                enriched_chunks.append(valid_chunk)
                print(f"         -> Fundet {len(valid_chunk)} gyldige kombinationer i denne bid.")

        if not enriched_chunks:
            print("    ❌ FEJL: Ingen gyldige bygningsposter fundet efter berigelse.")
            return

        # --- Trin 5: Saml alle resultater og aggreger bygningsdata ---
        print("    -> Samler resultater og summerer bygningsareal for hvert salg...")
        all_valid_bygninger = pd.concat(enriched_chunks, ignore_index=True)
        
        # Konverter arealer til numerisk før aggregering
        all_valid_bygninger['byg038SamletBygningsareal'] = pd.to_numeric(all_valid_bygninger['byg038SamletBygningsareal'], errors='coerce')
        
        # Definer aggregeringsfunktioner
        aggregation_functions = {
            'kontant_koebesum': 'first',
            'samlet_koebesum': 'first',
            'byg038SamletBygningsareal': 'sum' # Summer arealet af alle gyldige bygninger
        }
        
        # Grupper efter unikt salg og aggreger
        final_df = all_valid_bygninger.groupby(['bfeNummer', 'dato']).agg(aggregation_functions).reset_index()
        print(f"    -> {len(final_df)} unikke salg med aggregerede bygningsdata fundet.")

        # --- Trin 6: Filtrer for gyldig pris og areal ---
        print("    -> Filtrerer for at sikre gyldig pris og bygningsareal...")
        final_df['kontant_koebesum'] = pd.to_numeric(final_df['kontant_koebesum'], errors='coerce')
        final_df['samlet_koebesum'] = pd.to_numeric(final_df['samlet_koebesum'], errors='coerce')

        valid_area = final_df['byg038SamletBygningsareal'] > 0
        valid_price = (final_df['kontant_koebesum'] > 0) | (final_df['samlet_koebesum'] > 0)
        
        cleaned_df = final_df[valid_area & valid_price]
        print(f"    -> Efter rensning er der {len(cleaned_df)} poster tilbage.")
        
        # --- Trin 7: Vælg og omdøb kolonner ---
        final_df_renamed = cleaned_df.rename(columns={
            'bfeNummer': 'bfe_nummer',
            'kontant_koebesum': 'kontant_koebesum',
            'samlet_koebesum': 'samlet_koebesum',
            'byg038SamletBygningsareal': 'bygning_summeret_areal'
        })

        # --- Trin 8: Gem det endelige datasæt ---
        final_df_renamed.to_csv(final_output_path, index=False, encoding='utf-8')
        print(f"\n✅ Færdig. Datasæt med summeret bygningsareal gemt til '{final_output_path}'")

    except Exception as e:
        print(f"    ❌ Der opstod en uventet fejl: {e}")
        import traceback
        traceback.print_exc()

# ==============================================================================
# SCRIPT-EKSEKVERING
# ==============================================================================

if __name__ == "__main__":
    # --- Konfiguration ---
    RAW_DATA_FOLDER = './'
    PROCESSED_DATA_FOLDER = os.path.join(RAW_DATA_FOLDER, 'processed')
    SALES_FILE = 'sales_data3.csv'
    FINAL_CSV_PATH = os.path.join(RAW_DATA_FOLDER, 'building_area_price_data_summed.csv')

    start_time = time.time()
    
    preprocess_for_building_enrichment(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER)
    enrich_with_building_data(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER, SALES_FILE, FINAL_CSV_PATH)

    end_time = time.time()
    print(f"\nTotal eksekveringstid: {end_time - start_time:.2f} sekunder.")