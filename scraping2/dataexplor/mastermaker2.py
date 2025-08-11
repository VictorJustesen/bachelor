import pandas as pd
import time
import os
import math
import itertools

# Sæt pandas display-indstillinger for bedre fejlfinding
pd.options.display.max_columns = None

# ==============================================================================
# STADIE 1: FORBEHANDLING (Leveret af bruger og verificeret funktionel)
# ==============================================================================

def count_csv_rows(filepath):
    """Tæller effektivt antallet af rækker i en CSV-fil for statusopfølgning."""
    print(f"   Tæller rækker i {os.path.basename(filepath)}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Træk 1 fra for header-rækken
            return sum(1 for _ in f) - 1
    except Exception as e:
        print(f"   Kunne ikke tælle rækker for {os.path.basename(filepath)}: {e}")
        return None

def preprocess_bbr_files(data_folder, output_folder):
    """
    Læser store BBR CSV-filer i bidder, udvælger kun nødvendige kolonner,
    og gemmer dem som mindre, effektive CSV-filer. Springer over, hvis de allerede er behandlet.
    """
    print("--- Stadie 1: Forbehandling af store BBR-filer til mindre, effektive filer ---")
    
    files_to_process = {
        'Enhed.csv': {
            'usecols': [
                'id_lokalId', 'bygning', 'status', 'virkningFra', 'virkningTil',
                'enh020EnhedensAnvendelse', 'enh023Boligtype', 'enh026EnhedensSamledeAreal', 
                'enh027ArealTilBeboelse', 'enh031AntalVærelser', 'enh065AntalVandskylledeToiletter', 
                'enh033Badeforhold', 'enh034Køkkenforhold', 'etage'
            ],
            'dtype': {'id_lokalId': 'str', 'bygning': 'str', 'enh023Boligtype': 'str', 'etage': 'str'}
        },
  'Ejendomsrelation.csv': {
    # Add 'tinglystAreal' here
    'usecols': [
        'id_lokalId', 'bfeNummer', 'ejerlejlighed', 'samletFastEjendom', 
        'status', 'tinglystAreal', 'virkningFra', 'virkningTil'
    ],
    'dtype': {
        'id_lokalId': 'str', 'bfeNummer': 'float', 'ejerlejlighed': 'str', 
        'samletFastEjendom': 'str', 'tinglystAreal': 'float'
    }
},
        'EnhedEjendomsrelation.csv': {
            'usecols': ['enhed', 'ejerlejlighed', 'status'],
            'dtype': {'enhed': 'str', 'ejerlejlighed': 'str'}
        },
        'Bygning.csv': {
            'usecols': ['id_lokalId', 'byg026Opførelsesår', 'grund', 'byg038SamletBygningsareal', 'status', 'virkningFra','virkningTil', 'byg021BygningensAnvendelse'],
            'dtype': {'id_lokalId': 'str', 'grund': 'str'}
        },
        # **RETTELSE**: Tilføjet Grund.csv og BygningEjendomsrelation.csv som er nødvendige for korrekt mapping.
        'Grund.csv': {
            'usecols': ['id_lokalId', 'bestemtFastEjendom', 'status'],
            'dtype': {'id_lokalId': 'str', 'bestemtFastEjendom': 'str'}
        },
        
    }
    
    os.makedirs(output_folder, exist_ok=True)

    for filename, config in files_to_process.items():
        input_path = os.path.join(data_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.csv', '_trimmed.csv'))
        
        print(f"\n--> Tjekker for '{filename}'...")
        if os.path.exists(output_path):
            print(f"    ✅ Fandt eksisterende behandlet fil ved '{output_path}'. Springer over.")
            continue

        if not os.path.exists(input_path):
            print(f"    ⚠️ ADVARSEL: Filen '{filename}' blev ikke fundet i '{data_folder}'. Springer over.")
            continue

        print(f"    -> Ingen behandlet fil fundet. Starter behandling af '{filename}'...")
        try:
            chunk_size = 1000_000
            total_rows = count_csv_rows(input_path)
            total_chunks = math.ceil(total_rows / chunk_size) if total_rows is not None else 'N/A'
            print(f"    Totalt antal rækker: {total_rows}, Totalt antal bidder: {total_chunks}")

            reader = pd.read_csv(input_path, usecols=config['usecols'], dtype=config.get('dtype', {}), chunksize=chunk_size, low_memory=False)
            
            header_written = False
            for i, chunk in enumerate(reader, 1):
                print(f"    -> Behandler bid {i}/{total_chunks}...")
                if not header_written:
                    chunk.to_csv(output_path, index=False, mode='w', header=True)
                    header_written = True
                else:
                    chunk.to_csv(output_path, index=False, mode='a', header=False)
            
            if header_written:
                print(f"    ✅ Gemte trimmede data til '{output_path}'")
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"    ❌ FEJL under behandling af '{filename}': {e}")

# ==============================================================================
# STADIE 2: BERIGELSE VED HJÆLP AF BID-BASERET BEHANDLING
# ==============================================================================

def enrich_sales_data_in_chunks(raw_data_folder, processed_folder, sales_file, final_output_path):
    """
    Beriger salgsdata ved at behandle store BBR-filer i bidder for at sikre
    hukommelseseffektivitet, mens der bruges korrigeret logik for alle ejendomstyper.
    """
    print("\n--- Stadie 2: Berigelse af salgsdata ved hjælp af bid-baseret behandling ---")
    try:
        # --- 2.1: Indlæs alle nødvendige filer ---
        print("    -> Indlæser indledende relations- og oversættelsesfiler...")
        sales_df = pd.read_csv(os.path.join(raw_data_folder, sales_file), low_memory=False)
        ej_rel = pd.read_csv(os.path.join(processed_folder, 'Ejendomsrelation_trimmed.csv'), dtype=str, low_memory=False)
        enhed_ej_rel = pd.read_csv(os.path.join(processed_folder, 'EnhedEjendomsrelation_trimmed.csv'), dtype=str, low_memory=False)
        # **RETTELSE**: Indlæs de nye nødvendige filer
        grund_df = pd.read_csv(os.path.join(processed_folder, 'Grund_trimmed.csv'), dtype=str, low_memory=False)

        # --- 2.2: Forbered og rens indledende data ---
        sales_df.rename(columns={'bfe_nummer': 'bfeNummer'}, inplace=True)
        sales_df['dato'] = pd.to_datetime(sales_df['dato'], errors='coerce', utc=True)
        sales_df.dropna(subset=['dato', 'bfeNummer'], inplace=True)
        sales_df['bfeNummer'] = pd.to_numeric(sales_df['bfeNummer'], errors='coerce').astype('Int64')
        ej_rel['bfeNummer'] = pd.to_numeric(ej_rel['bfeNummer'], errors='coerce').astype('Int64')
        ej_rel.dropna(subset=['bfeNummer', 'id_lokalId'], inplace=True)
        print(f"    -> Indlæst og forberedt {len(sales_df)} salgsposter.")

        # --- 2.3: Byg opslags-maps fra BBR-data ved hjælp af korrekt logik ---
        print("    -> Bygger opslags-maps med korrekte ID'er...")
        # STI A: Ejerlejligheder (Apartments)
        # Sammenflet ejendomsrelation (for BFE) med enhed-ejendom relation (for enheds-ID)
        condo_map_df = pd.merge(ej_rel, enhed_ej_rel, left_on='id_lokalId', right_on='ejerlejlighed')
        condo_map_df.drop_duplicates(subset=['bfeNummer'], keep='first', inplace=True)
        bfe_to_enhed_map = condo_map_df.set_index('bfeNummer')['enhed'].to_dict()

        # STI B: Bygninger på egen grund (Villas etc.)
        bfe_to_property_uuid_map = ej_rel.drop_duplicates(subset=['bfeNummer']).set_index('bfeNummer')['id_lokalId'].to_dict()
        property_uuid_to_grund_uuid_map = grund_df.drop_duplicates(subset=['bestemtFastEjendom']).set_index('bestemtFastEjendom')['id_lokalId'].to_dict()
        
        # STI C: Bygninger på fremmed grund (Special Case)

        # --- 2.4: Byg bygnings-maps ---
        print("    -> Behandler Bygning.csv i bidder for at bygge bygnings-maps...")
        bygning_reader = pd.read_csv(os.path.join(processed_folder, 'Bygning_trimmed.csv'), chunksize=500_000, low_memory=False)
        grund_uuid_to_building_map = {}
        building_attribute_map = {}

        for i, chunk in enumerate(bygning_reader, 1):
            print(f"       -> Behandler Bygning-bid {i}...")
            chunk.dropna(subset=['grund', 'id_lokalId'], inplace=True)
            unique_grund_chunk = chunk.drop_duplicates(subset=['grund'], keep='first')
            grund_uuid_to_building_map.update(unique_grund_chunk.set_index('grund')['id_lokalId'].to_dict())
            unique_id_chunk = chunk.drop_duplicates(subset=['id_lokalId'], keep='first')
            building_attribute_map.update(unique_id_chunk.set_index('id_lokalId')[['byg026Opførelsesår', 'byg038SamletBygningsareal']].to_dict('index'))
        
        # --- 2.5: Forbered salgs-DataFrame med fuld mapping ---
        print("    -> Mapper salg til BBR-enheder...")
        # Map lejligheder direkte til enheds-ID
        sales_df['enhed_id'] = sales_df['bfeNummer'].map(bfe_to_enhed_map)
        
        # Map andre ejendomme til bygnings-ID via Grund
        sales_df['property_uuid'] = sales_df['bfeNummer'].map(bfe_to_property_uuid_map)
        sales_df['grund_uuid'] = sales_df['property_uuid'].map(property_uuid_to_grund_uuid_map)
        sales_df['bygning_id_grund'] = sales_df['grund_uuid'].map(grund_uuid_to_building_map)

        # Map bygninger på fremmed grund
        
        # Kombiner bygnings-ID'er. `bygning_id_grund` har forrang.
        sales_df['bygning_id'] = sales_df['bygning_id_grund']
        
        apartment_sales = sales_df[sales_df['enhed_id'].notna()].copy()
        villa_sales = sales_df[sales_df['bygning_id'].notna() & sales_df['enhed_id'].isna()].copy()
        print(f"    -> Identificeret {len(apartment_sales)} ejerlejlighedssalg og {len(villa_sales)} andre bygningssalg.")

        # --- 2.6: Hovedberigelsesløkke, der behandler Enhed.csv i bidder ---
        print("    -> Starter hovedberigelse ved at behandle Enhed.csv i bidder...")
        enhed_reader = pd.read_csv(os.path.join(processed_folder, 'Enhed_trimmed.csv'), chunksize=500_000, low_memory=False, dtype=str)
        enriched_chunks = []
        debug_info_printed = False
        
        pre_2000_virkningFra_count = 0
        pre_2000_virkningTil_count = 0
        pre_2001_virkningFra_count = 0
        pre_2001_virkningTil_count = 0
        pre_2002_virkningFra_count = 0
        pre_2002_virkningTil_count = 0
        sum_valid_apartments = 0
        sum_valid_villas = 0

        # **NYT**: Initialiser sæt til at spore kasserede BFE-numre
        discarded_due_to_history_bfe = set()

        for i, enhed_chunk in enumerate(enhed_reader, 1):
            print(f"       -> Behandler Enhed-bid {i}...")
            enhed_chunk['virkningFra'] = pd.to_datetime(enhed_chunk['virkningFra'], errors='coerce', utc=True)
            enhed_chunk['virkningTil'] = pd.to_datetime(enhed_chunk['virkningTil'], errors='coerce', utc=True)
            
            pre_2000_virkningFra_count += (enhed_chunk['virkningFra'].dt.year < 2000).sum()
            pre_2000_virkningTil_count += (enhed_chunk['virkningTil'].dt.year < 2000).sum()
            pre_2001_virkningFra_count += (enhed_chunk['virkningFra'].dt.year < 2001).sum()
            pre_2001_virkningTil_count += (enhed_chunk['virkningTil'].dt.year < 2001).sum()
            pre_2002_virkningFra_count += (enhed_chunk['virkningFra'].dt.year < 2002).sum()
            pre_2002_virkningTil_count += (enhed_chunk['virkningTil'].dt.year < 2002).sum()

            enriched_apartments = pd.merge(apartment_sales, enhed_chunk, left_on='enhed_id', right_on='id_lokalId', how='inner')
            enriched_villas = pd.merge(villa_sales, enhed_chunk, left_on='bygning_id', right_on='bygning', how='inner')
            
            combined_chunk = pd.concat([enriched_apartments, enriched_villas], ignore_index=True)
            
            if not combined_chunk.empty:
                cutoff_date = pd.Timestamp('2002-01-01', tz='UTC')

                query_str = "(virkningFra <= dato) and (dato < virkningTil or virkningTil.isnull())"
                valid_records = combined_chunk.query(query_str).copy()
                
                # Find de kasserede poster for denne bid
                rejected_records = combined_chunk.drop(valid_records.index)
                
                # **NYT**: Opdater sættet med unikke BFE-numre, der blev kasseret
                if not rejected_records.empty:
                    discarded_due_to_history_bfe.update(rejected_records['bfeNummer'].unique())

                if not debug_info_printed and not rejected_records.empty:
                    print("\n    --- 🕵️ Debugging af kasserede poster (viser op til 5 eksempler fra første bid) ---")
                    for idx, row in rejected_records.head(5).iterrows():
                        sale_date, bbr_start, bbr_end = row['dato'], row['virkningFra'], row['virkningTil']
                        reason = f"Salgsdato ({sale_date.date()}) er uden for BBR-postens gyldighed ({bbr_start.date()} til {bbr_end.date() if pd.notna(bbr_end) else 'nu'})."
                        print(f"      - Kasseret BFE {row['bfeNummer']}: {reason}")
                    print("    -------------------------------------------------------------------------------------\n")
                    debug_info_printed = True
                
                if not valid_records.empty:
                    # **NYT**: Print opdelingen af gyldige poster for denne bid
                    valid_apartments = valid_records['enhed_id'].notna().sum()
                    valid_villas = valid_records['enhed_id'].isna().sum()
                    sum_valid_apartments += valid_apartments
                    sum_valid_villas += valid_villas
                    print(f"       -> Gyldige poster i denne bid: {len(valid_records)} (Lejligheder: {valid_apartments}, Villaer: {valid_villas})")
                    enriched_chunks.append(valid_records)

        print("\n    --- 📊 BBR Dato-analyse (Enhed.csv) ---")
        print(f"    Antal BBR-poster med startdato (`virkningFra`) før år 2000: {pre_2000_virkningFra_count}")
        print(f"    Antal BBR-poster med slutdato (`virkningTil`) før år 2000: {pre_2000_virkningTil_count}")
        print(f"    Antal BBR-poster med startdato (`virkningFra`) før år 2001: {pre_2001_virkningFra_count}")
        print(f"    Antal BBR-poster med slutdato (`virkningTil`) før år 2001: {pre_2001_virkningTil_count}")
        print(f"    Antal BBR-poster med startdato (`virkningFra`) før år 2002: {pre_2002_virkningFra_count}")
        print(f"    Antal BBR-poster med slutdato (`virkningTil`) før år 2002: {pre_2002_virkningTil_count}")
        print("    -------------------------------------------\n")

        # **NYT**: Print det endelige antal unikke BFE-numre, der blev kasseret pga. historik
        print(f"    --- 📉 Opsummering af kasserede salg ---")
        print(f"    Antal unikke BFE-numre kasseret pga. ugyldig historik: {len(discarded_due_to_history_bfe)}")
        print(f"    antal lejlighedssalg med gyldig historik: {sum_valid_apartments}")
        print(f"    antal villaer med gyldig historik: {sum_valid_villas}")
        print("    ------------------------------------------\n")

        if not enriched_chunks:
            print("    ❌ FEJL: Ingen gyldige poster fundet efter berigelse. Processen kan ikke fortsætte.")
            return

        # --- 2.7: Endelig samling og oprydning ---
        print("    -> Samler endeligt datasæt...")
        final_df = pd.concat(enriched_chunks, ignore_index=True)
        # Sørg for at hver salg kun har én matchende BBR-registrering
        final_df.drop_duplicates(subset=['bfeNummer', 'dato'], keep='first', inplace=True)
        print(f"    -> Fundet {len(final_df)} historisk gyldige, berigede salgsposter.")
        print(f" endelig antal lejlighedssalg: {len(final_df[final_df['enhed_id'].notna()])}")
        # Tilføj bygningsattributter til det endelige datasæt
        final_df['construction_year'] = final_df['bygning_id'].map({k: v['byg026Opførelsesår'] for k, v in building_attribute_map.items()})
        final_df['building_area'] = final_df['bygning_id'].map({k: v['byg038SamletBygningsareal'] for k, v in building_attribute_map.items()})
        
        # Tilføj grundareal fra den oprindelige ejendomsrelation
        bfe_to_area_map = ej_rel.set_index('bfeNummer')['tinglystAreal'].to_dict() # Antager at tinglystAreal findes i ej_rel
        final_df['tinglystAreal'] = final_df['bfeNummer'].map(bfe_to_area_map)

        # Færdiggør kolonner og gem
        column_mapping = {
            'bfeNummer': 'bfe_nummer', 'kontant_koebesum': 'kontant_koebesum',
            'samlet_koebesum': 'samlet_koebesum', 'loesoeresum': 'loesoeresum',
            'salgstype': 'salgstype', 'dato': 'dato', 'kommunekode': 'kommunekode',
            'tinglystAreal': 'grund_areal', 'bygning_id': 'bygning_id', 'id_lokalId': 'enhed_id',
            'enh023Boligtype': 'hustype', 'enh027ArealTilBeboelse': 'livable_area_at_sale',
            'enh031AntalVærelser': 'rooms_at_sale', 'enh065AntalVandskylledeToiletter': 'toilets_at_sale',
            'enh033Badeforhold': 'badeforhold', 'enh034Køkkenforhold': 'koekkenforhold',
            'etage': 'etage', 'construction_year': 'construction_year',
            'building_area': 'building_area', 'tinglystAreal': 'tinglyst_areal'
        }
        
        final_columns = [col for col in column_mapping.keys() if col in final_df.columns]
        final_df_renamed = final_df[final_columns].rename(columns=column_mapping)
        
        final_df_renamed.to_csv(final_output_path, index=False, encoding='utf-8')
        print(f"\n✅ Færdig. Endeligt datasæt med {len(final_df_renamed)} poster gemt til '{final_output_path}'")

    except FileNotFoundError as e:
        print(f"    ❌ FIL IKKE FUNDET: {e}. Sørg for at alle nødvendige BBR-filer findes i '{processed_folder}' og salgsfilen i '{raw_data_folder}'.")
    except Exception as e:
        import traceback
        print(f"    ❌ Der opstod en uventet fejl under berigelsesfasen: {e}")
        traceback.print_exc()

# ==============================================================================
# SCRIPT-EKSEKVERING
# ==============================================================================

if __name__ == "__main__":
    # --- Konfiguration ---
    RAW_DATA_FOLDER = './'
    PROCESSED_DATA_FOLDER = os.path.join(RAW_DATA_FOLDER, 'processed')
    SALES_FILE = 'sales_data3.csv'
    FINAL_CSV_PATH = os.path.join(RAW_DATA_FOLDER, 'final_enriched_sales_data_v16.csv')

    start_time = time.time()
    
    # Stadie 1: Forbehandl rå CSV-filer til mindre, trimmede CSV-filer.
    preprocess_bbr_files(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER)
    
    # Stadie 2: Berig salgsdata ved hjælp af den hukommelseseffektive bid-metode.
    enrich_sales_data_in_chunks(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER, SALES_FILE, FINAL_CSV_PATH)

    end_time = time.time()
    print(f"\nTotal eksekveringstid: {end_time - start_time:.2f} sekunder.")