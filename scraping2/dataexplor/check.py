import ijson
import json

def search_for_bfe_number(input_path, target_bfe):
    print(f"🔍 Searching for BFE number {target_bfe} in {input_path}...")
    
    found_sales = []
    found_ejerskifte = []
    found_ejerskab = []
    
    try:
        with open(input_path, 'rb') as f:
            # Search in HandelsoplysningerList
            print("-> Checking HandelsoplysningerList...")
            handelsoplysninger_items = ijson.items(f, 'HandelsoplysningerList.item')
            for handel in handelsoplysninger_items:
                # Note: HandelsoplysningerList doesn't directly contain BFE numbers
                # We need to cross-reference with EjerskifteList
                found_sales.append({
                    'id': handel.get('id_lokalId'),
                    'kontant_pris': handel.get("kontantKoebesum"),
                    'samlet_pris': handel.get("samletKoebesum"),
                })
        
        with open(input_path, 'rb') as f:
            # Search in EjerskifteList (this contains BFE numbers)
            print("-> Checking EjerskifteList...")
            ejerskifte_items = ijson.items(f, 'EjerskifteList.item')
            for ejerskifte in ejerskifte_items:
                bfe_nummer = ejerskifte.get("bestemtFastEjendomBFENr")
                if bfe_nummer == target_bfe:
                    found_ejerskifte.append({
                        'bfe_nummer': bfe_nummer,
                        'handelsoplysninger_id': ejerskifte.get("handelsoplysningerLokalId"),
                        'status': ejerskifte.get("status"),
                        'overdragelsesmaade': ejerskifte.get("overdragelsesmaade"),
                        'anmeldelsesdato': ejerskifte.get("anmeldelsesdato"),
                        'overtagelsesdato': ejerskifte.get("overtagelsesdato"),
                        'betinget': ejerskifte.get("betinget")
                    })
        
        with open(input_path, 'rb') as f:
            # Search in EjerskabList
            print("-> Checking EjerskabList...")
            ejerskab_items = ijson.items(f, 'EjerskabList.item')
            for ejerskab in ejerskab_items:
                bfe_nummer = ejerskab.get("bestemtFastEjendomBFENr")
                if bfe_nummer == target_bfe:
                    found_ejerskab.append({
                        'bfe_nummer': bfe_nummer,
                        'ejer_type': 'company' if ejerskab.get("ejendeVirksomhedCVRNr") else 'individual',
                        'cvr': ejerskab.get("ejendeVirksomhedCVRNr")
                    })
    
    except FileNotFoundError:
        print(f"❌ Error: File not found at {input_path}")
        return
    
    # Print results
    print(f"\n📊 RESULTS for BFE {target_bfe}:")
    print(f"{'='*50}")
    
    if found_ejerskifte:
        print(f"✅ Found {len(found_ejerskifte)} transaction(s) in EjerskifteList:")
        for i, item in enumerate(found_ejerskifte, 1):
            print(f"  Transaction {i}:")
            print(f"    BFE: {item['bfe_nummer']}")
            print(f"    Handelsoplysninger ID: {item['handelsoplysninger_id']}")
            print(f"    Status: {item['status']}")
            print(f"    Sale Type: {item['overdragelsesmaade']}")
            print(f"    Filing Date: {item['anmeldelsesdato']}")
            print(f"    Transfer Date: {item['overtagelsesdato']}")
            print(f"    Conditional: {item['betinget']}")
            
            # Try to find corresponding price data
            handel_id = item['handelsoplysninger_id']
            matching_sale = next((s for s in found_sales if s['id'] == handel_id), None)
            if matching_sale:
                print(f"    💰 Kontant Price: {matching_sale['kontant_pris']}")
                print(f"    💰 Total Price: {matching_sale['samlet_pris']}")
            print()
    else:
        print(f"❌ No transactions found for BFE {target_bfe} in EjerskifteList")
    
    if found_ejerskab:
        print(f"✅ Found {len(found_ejerskab)} ownership record(s) in EjerskabList:")
        for i, item in enumerate(found_ejerskab, 1):
            print(f"  Ownership {i}:")
            print(f"    BFE: {item['bfe_nummer']}")
            print(f"    Owner Type: {item['ejer_type']}")
            if item['cvr']:
                print(f"    Company CVR: {item['cvr']}")
            print()
    else:
        print(f"❌ No ownership records found for BFE {target_bfe} in EjerskabList")

if __name__ == "__main__":
    INPUT_FILE_PATH = './test_tdyt_1__20250627184206.json'
    TARGET_BFE = 249142
    
    search_for_bfe_number(INPUT_FILE_PATH, TARGET_BFE)