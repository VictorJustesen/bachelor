import ijson
import json
import time

def build_company_property_exclusion_list(input_path):
    print("Step 1: Identifying company-owned properties to exclude...")
    company_bfe_set = set()
    try:
        with open(input_path, 'rb') as f:
            ejerskab_items = ijson.items(f, 'EjerskabList.item')
            for ejerskab in ejerskab_items:
                if ejerskab.get("ejendeVirksomhedCVRNr") is not None:
                    bfe_nummer = ejerskab.get("bestemtFastEjendomBFENr")
                    if bfe_nummer:
                        company_bfe_set.add(bfe_nummer)
        print(f"-> Found {len(company_bfe_set)} company-owned properties to exclude.")
        return company_bfe_set
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        return None

def create_simplified_sales_data(input_path, output_path, company_bfe_set):
    print("\nStep 2: Creating highly filtered sales data file...")

    VALID_SALE_TYPES = {'Almindelig fri handel'}

    print("-> Pass 1/2: Scanning transactions to build a lookup map of valid sales...")
    sales_lookup = {}
    with open(input_path, 'rb') as f:
        ejerskifte_items = ijson.items(f, 'EjerskifteList.item')
        for ejerskifte in ejerskifte_items:
            is_valid_status = ejerskifte.get("status") in {"gældende", "historisk"}
            is_not_conditional = not ejerskifte.get("betinget")
            is_normal_sale_type = ejerskifte.get("overdragelsesmaade") in VALID_SALE_TYPES
            
            if is_valid_status and is_not_conditional and is_normal_sale_type:
                bfe_nummer = ejerskifte.get("bestemtFastEjendomBFENr")
                if bfe_nummer not in company_bfe_set:
                    hid = ejerskifte.get("handelsoplysningerLokalId")
                    if hid:
                        sales_lookup[hid] = {
                            "bfe_nummer": bfe_nummer,
                            "salgstype": ejerskifte.get("overdragelsesmaade")
                        }
    print(f"-> Found {len(sales_lookup)} valid, non-conditional, normal-trade transactions.")

    print("-> Pass 2/2: Writing simplified and filtered sales data...")
    with open(output_path, 'w', encoding='utf-8') as out_f:
        is_first_item = True
        out_f.write('[')

        with open(input_path, 'rb') as in_f:
            handelsoplysninger_items = ijson.items(in_f, 'HandelsoplysningerList.item')
            for handel in handelsoplysninger_items:
                handel_id = handel.get('id_lokalId')
                if handel_id in sales_lookup:
                    
                    kontant_pris = handel.get("kontantKoebesum")
                    samlet_pris = handel.get("samletKoebesum")

                    # Keep the record if at least one of the prices is valid and positive
                    has_valid_price = (kontant_pris is not None and kontant_pris > 0) or \
                                      (samlet_pris is not None and samlet_pris > 0)

                    if has_valid_price:
                        if not is_first_item:
                            out_f.write(',')
                        
                        simplified_sale = {
                            "bfe_nummer": sales_lookup[handel_id]["bfe_nummer"],
                            "kontant_koebesum": kontant_pris,
                            "samlet_koebesum": samlet_pris,
                            "loesoeresum": handel.get("loesoeresum"),
                            "salgstype": sales_lookup[handel_id]["salgstype"],
                            "dato": handel.get("overtagelsesdato") or handel.get("koebsaftaleDato")
                        }
                        
                        json.dump(simplified_sale, out_f, ensure_ascii=False)
                        is_first_item = False
        
        out_f.write(']')

    print(f"\n✅ Successfully created highly filtered data file at: {output_path}")


if __name__ == "__main__":
    INPUT_FILE_PATH = './test_tdyt_1__20250627184206.json'
    OUTPUT_FILE_PATH = './filtered_with_both_prices.json'

    start_time = time.time()
    
    company_properties = build_company_property_exclusion_list(INPUT_FILE_PATH)
    
    if company_properties is not None:
        create_simplified_sales_data(INPUT_FILE_PATH, OUTPUT_FILE_PATH, company_properties)

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")