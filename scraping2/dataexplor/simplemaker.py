import pandas as pd
import os
import time

def create_simple_area_price_data(raw_data_folder, processed_folder, sales_file, final_output_path):
    """
    Kombinerer salgsdata med historiske ejendomsrelationsdata og filtrerer for at sikre,
    at alle poster har en gyldig pris og et gyldigt tinglyst areal.
    """
    print("--- Starter sammensætning af pris og historisk korrekt tinglyst areal ---")
    
    try:
        # --- Trin 1: Indlæs de nødvendige filer ---
        print("    -> Indlæser salgsdata og ejendomsrelationer...")
        sales_path = os.path.join(raw_data_folder, sales_file)
        ej_rel_path = os.path.join(processed_folder, 'Ejendomsrelation_trimmed.csv')

        if not os.path.exists(sales_path):
            print(f"    ❌ FEJL: Salgsfilen blev ikke fundet ved '{sales_path}'")
            return
        if not os.path.exists(ej_rel_path):
            print(f"    ❌ FEJL: Ejendomsrelation_trimmed.csv blev ikke fundet ved '{ej_rel_path}'.")
            print("         Kør venligst det oprindelige, fulde script først for at generere denne fil.")
            return

        sales_df = pd.read_csv(sales_path, low_memory=False)
        ej_rel_df = pd.read_csv(ej_rel_path, low_memory=False)

        # --- Trin 2: Forbered data til merge ---
        print("    -> Forbereder og konverterer datoer...")
        sales_df.rename(columns={'bfe_nummer': 'bfeNummer'}, inplace=True)

        sales_df['dato'] = pd.to_datetime(sales_df['dato'], errors='coerce', utc=True)
        ej_rel_df['virkningFra'] = pd.to_datetime(ej_rel_df['virkningFra'], errors='coerce', utc=True)
        ej_rel_df['virkningTil'] = pd.to_datetime(ej_rel_df['virkningTil'], errors='coerce', utc=True)

        sales_df['bfeNummer'] = pd.to_numeric(sales_df['bfeNummer'], errors='coerce')
        ej_rel_df['bfeNummer'] = pd.to_numeric(ej_rel_df['bfeNummer'], errors='coerce')

        sales_df.dropna(subset=['bfeNummer', 'dato'], inplace=True)
        ej_rel_df.dropna(subset=['bfeNummer', 'virkningFra'], inplace=True)
        
        sales_df['bfeNummer'] = sales_df['bfeNummer'].astype('int64')
        ej_rel_df['bfeNummer'] = ej_rel_df['bfeNummer'].astype('int64')

        # --- Trin 3: Merge de to dataframes ---
        print(f"    -> Merger {len(sales_df)} salg med {len(ej_rel_df)} historiske ejendomsposter...")
        merged_df = pd.merge(sales_df, ej_rel_df, on='bfeNummer', how='inner')
        print(f"    -> Merge resulterede i {len(merged_df)} potentielle kombinationer.")

        # --- Trin 4: Anvend historisk filter ---
        print("    -> Anvender historisk filter for at finde den korrekte post for hver salgsdato...")
        query_str = "virkningFra <= dato and (dato < virkningTil or virkningTil.isnull())"
        valid_records_df = merged_df.query(query_str)
        print(f"    -> Fundet {len(valid_records_df)} salg-til-BBR kombinationer med gyldig historik.")

        # --- Trin 5: Fjern duplikater for at sikre én post per salg ---
        final_df = valid_records_df.drop_duplicates(subset=['bfeNummer', 'dato'], keep='first').copy()
        print(f"    -> Efter fjernelse af duplikater er der {len(final_df)} unikke, berigede salg tilbage.")

        # --- Trin 6: **NYT** Filtrer for gyldigt areal og pris ---
        print("    -> Filtrerer for at sikre gyldigt areal og pris...")
        
        # Konverter pris- og arealkolonner til numerisk, sæt ugyldige værdier til NaN
        final_df['kontant_koebesum'] = pd.to_numeric(final_df['kontant_koebesum'], errors='coerce')
        final_df['samlet_koebesum'] = pd.to_numeric(final_df['samlet_koebesum'], errors='coerce')
        final_df['tinglystAreal'] = pd.to_numeric(final_df['tinglystAreal'], errors='coerce')

        # Definer gyldighedsbetingelser
        valid_area_condition = final_df['tinglystAreal'] > 0
        valid_price_condition = (final_df['kontant_koebesum'] > 0) | (final_df['samlet_koebesum'] > 0)
        
        # Anvend filteret
        cleaned_df = final_df[valid_area_condition & valid_price_condition]
        print(f"    -> Efter rensning er der {len(cleaned_df)} poster med både gyldigt areal og pris.")

        # --- Trin 7: Vælg og omdøb de endelige kolonner ---
        final_df_renamed = cleaned_df[[
            'bfeNummer',
            'dato',
            'kontant_koebesum',
            'samlet_koebesum',
            'tinglystAreal'
        ]].copy()

        final_df_renamed.rename(columns={
            'bfeNummer': 'bfe_nummer',
            'kontant_koebesum': 'kontant_koebesum',
            'samlet_koebesum': 'samlet_koebesum',
            'tinglystAreal': 'tinglyst_areal'
        }, inplace=True)

        # --- Trin 8: Gem det endelige, simple datasæt ---
        final_df_renamed.to_csv(final_output_path, index=False, encoding='utf-8')
        print(f"\n✅ Færdig. Renset, historisk korrekt datasæt med {len(final_df_renamed)} poster gemt til '{final_output_path}'")

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
    FINAL_CSV_PATH = os.path.join(RAW_DATA_FOLDER, 'area_price_data_cleaned_and_correct.csv')

    start_time = time.time()
    
    # Kør den simple sammensætningsfunktion
    create_simple_area_price_data(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER, SALES_FILE, FINAL_CSV_PATH)

    end_time = time.time()
    print(f"\nTotal eksekveringstid: {end_time - start_time:.2f} sekunder.")