import requests
import json
import re

class DanishAddressParser:
    """Enhanced Danish address parser for better DAWA integration"""
    
    def __init__(self):
        self.dawa_base_url = "https://api.dataforsyningen.dk/adresser"
    
    def parse_danish_address(self, address_string):
        """Parse Danish address into components"""
        # Clean up the address first - remove commas and periods
        cleaned = address_string.strip()
        cleaned = cleaned.replace(',', ' ')  # Remove commas
        cleaned = cleaned.replace('.', '')   # Remove periods
        cleaned = ' '.join(cleaned.split())  # Normalize whitespace
        
        result = {
            'vejnavn': None,
            'husnr': None,
            'etage': None,
            'dør': None,
            'postnr': None,
            'city': None,
            'original': address_string,
            'cleaned': cleaned
        }
        
        # Find postal code (4 digits)
        postal_code_pattern = r'\b\d{4}\b'
        postal_matches = list(re.finditer(postal_code_pattern, cleaned))
        
        if postal_matches:
            postal_match = postal_matches[-1]
            result['postnr'] = postal_match.group()
            postal_index = postal_match.start()
            
            # Everything after postal code is city
            city_part = cleaned[postal_match.end():].strip()
            if city_part:
                result['city'] = city_part
            
            # Everything before postal code contains address
            address_part = cleaned[:postal_index].strip()
        else:
            address_part = cleaned
        
        # Parse the address part
        address_parts = address_part.split()
        
        if not address_parts:
            return result
        
        # Find house number (first number in the address part)
        house_number_pattern = r'\b\d+[A-Za-z]?\b'
        
        street_name_parts = []
        remaining_parts = []
        house_number_found = False
        
        for i, part in enumerate(address_parts):
            if re.match(house_number_pattern, part) and not house_number_found:
                result['husnr'] = part
                house_number_found = True
                remaining_parts = address_parts[i+1:]
                break
            else:
                street_name_parts.append(part)
        
        if street_name_parts:
            result['vejnavn'] = ' '.join(street_name_parts)
        
        # Parse remaining parts for floor and door
        if remaining_parts:
            # Simplified patterns since we cleaned punctuation
            floor_patterns = [r'^(st|kl|k[2-9])$', r'^\d{1,2}$']
            door_patterns = [r'^(tv|th)$', r'^\d{1,4}$', r'^[a-z]$', r'^\d+-\d+$', r'^\d+[a-z]$']
            
            i = 0
            while i < len(remaining_parts):
                part = remaining_parts[i].lower()
                
                if not result['etage'] and any(re.match(pattern, part) for pattern in floor_patterns):
                    result['etage'] = part
                elif not result['dør'] and any(re.match(pattern, part) for pattern in door_patterns):
                    result['dør'] = part
                
                i += 1
        
        return result
    
    def search_address_dawa(self, address_string):
        """Search for address using DAWA API with enhanced parsing"""
        parsed = self.parse_danish_address(address_string)
        
        print(f"🧹 Cleaned address: '{parsed['cleaned']}'")
        print(f"🧩 Parsed components: {dict((k,v) for k,v in parsed.items() if v and k not in ['original', 'cleaned'])}")
        
        # Try specific component search first
        params = {'struktur': 'mini'}
        
        if parsed['vejnavn']:
            params['vejnavn'] = parsed['vejnavn']
        if parsed['husnr']:
            params['husnr'] = parsed['husnr']
        if parsed['etage']:
            params['etage'] = parsed['etage']
        if parsed['dør']:
            params['dør'] = parsed['dør']
        if parsed['postnr']:
            params['postnr'] = parsed['postnr']
        
        try:
            print(f"🔍 Enhanced search with components: {params}")
            response = requests.get(self.dawa_base_url, params=params)
            response.raise_for_status()
            results = response.json()
            
            if results:
                print(f"✅ Found {len(results)} results with component search")
                return results, parsed
            
        except Exception as e:
            print(f"⚠️ Component search failed: {e}")
        
        # Fallback to general text search using cleaned address
        fallback_params = {'q': parsed['cleaned'], 'struktur': 'mini'}
        
        try:
            print(f"🔍 Fallback search with cleaned text: '{parsed['cleaned']}'")
            response = requests.get(self.dawa_base_url, params=fallback_params)
            response.raise_for_status()
            results = response.json()
            
            print(f"✅ Found {len(results)} results with fallback search")
            return results, parsed
            
        except Exception as e:
            print(f"❌ All searches failed: {e}")
            return [], parsed

def find_best_address_match(dawa_results, parsed_components):
    """Find the best matching address from DAWA results with corrected structure handling"""
    
    if not dawa_results:
        print("❌ No DAWA results to analyze")
        return None
    
    print(f"🔍 Analyzing {len(dawa_results)} results to find best match...")
    
    for i, result in enumerate(dawa_results):
        print(f"  📋 Result {i+1}: {result.get('betegnelse', result.get('adressebetegnelse', 'No address'))}")
        print(f"    🆔 Address ID: {result.get('id', 'No ID')}")
        print(f"    🏠 Adgangsadresse ID: {result.get('adgangsadresseid', 'No adgangsadresse ID')}")
        
        # Check for adgangsadresseid (the correct field in DAWA mini structure)
        if 'adgangsadresseid' in result and result['adgangsadresseid']:
            print(f"    ✅ Valid result found with adgangsadresseid: {result['adgangsadresseid']}")
            return result
        
        # Fallback: check for nested adgangsadresse structure (older format)
        elif 'adgangsadresse' in result and isinstance(result['adgangsadresse'], dict):
            if 'id' in result['adgangsadresse']:
                print(f"    ✅ Valid result found with nested structure: {result['adgangsadresse']['id']}")
                return result
        
        print(f"    ⚠️ Result missing valid adgangsadresse ID")
    
    # If no valid result found, return the first one anyway and let caller handle it
    print("❌ No results with proper adgangsadresse structure found, using first result")
    return dawa_results[0] if dawa_results else None

def get_property_data_enhanced(full_address_string, service_username, service_password):
    """Enhanced property data fetcher with corrected DAWA structure handling"""
    
    print("=" * 80)
    print(f"🏠 ENHANCED PROPERTY DATA SEARCH FOR: {full_address_string}")
    print("=" * 80)
    
    # Step 1: Enhanced address search
    print("\n--- Step 1: Enhanced Address Search via DAWA ---")
    
    parser = DanishAddressParser()
    dawa_results, parsed_components = parser.search_address_dawa(full_address_string)
    
    if not dawa_results:
        print("❌ Could not find address in DAWA")
        return None
    
    # Find the best valid match
    best_match = find_best_address_match(dawa_results, parsed_components)
    
    if not best_match:
        print("❌ No valid address match found in DAWA results")
        return None
    
    # Extract adgangsadresse ID using the correct field
    adgangsadresse_id = None
    
    if 'adgangsadresseid' in best_match:
        adgangsadresse_id = best_match['adgangsadresseid']
    elif 'adgangsadresse' in best_match and isinstance(best_match['adgangsadresse'], dict):
        adgangsadresse_id = best_match['adgangsadresse'].get('id')
    
    if not adgangsadresse_id:
        print("❌ Could not extract adgangsadresse ID from result")
        print(f"Available keys: {list(best_match.keys())}")
        return None
    
    print(f"✅ Found address: {best_match.get('betegnelse', best_match.get('adressebetegnelse', 'Unknown'))}")
    print(f"📍 Address ID: {best_match.get('id', 'Unknown')}")
    print(f"🏠 Adgangsadresse ID: {adgangsadresse_id}")
    
    # Step 2: BBR Building Data
    print("\n--- Step 2: Fetching BBR Building Data ---")
    
    bygning_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning"
    bygning_params = {
        "Husnummer": adgangsadresse_id,
        "username": service_username,
        "password": service_password
    }
    
    try:
        response_bygning = requests.get(bygning_endpoint, params=bygning_params)
        response_bygning.raise_for_status()
        bygning_data = response_bygning.json()
        
        if not bygning_data:
            print("⚠️ No BBR building data found")
            building_details = []
        else:
            print(f"✅ Found {len(bygning_data)} building(s)")
            building_details = extract_building_details(bygning_data, service_username, service_password)
            
    except Exception as e:
        print(f"❌ Error fetching building data: {e}")
        building_details = []
    
    # Step 3: BFE Number
    print("\n--- Step 3: Getting BFE Property Number ---")
    
    try:
        bfe_nummer = get_bfe_number(adgangsadresse_id, service_username, service_password)
        if bfe_nummer:
            print(f"✅ BFE Number: {bfe_nummer}")
        else:
            print("⚠️ Could not find BFE number")
    except Exception as e:
        print(f"❌ Error getting BFE number: {e}")
        bfe_nummer = None
    
    # Step 4: Sales History
    print("\n--- Step 4: Fetching Sales History ---")
    
    sales_history = []
    if bfe_nummer:
        try:
            sales_history = get_sales_history(bfe_nummer, service_username, service_password)
            if sales_history:
                print(f"✅ Found {len(sales_history)} sales record(s)")
                for sale in sales_history[:3]:  # Show first 3
                    print(f"  📅 {sale.get('handelsdato')}: {sale.get('koebesum')} DKK")
            else:
                print("ℹ️ No sales history found")
        except Exception as e:
            print(f"❌ Error fetching sales history: {e}")
    
    # Compile comprehensive result
    result = {
        'search_query': full_address_string,
        'parsed_address': parsed_components,
        'dawa_result': best_match,
        'adgangsadresse_id': adgangsadresse_id,
        'building_data': building_details,
        'bfe_number': bfe_nummer,
        'sales_history': sales_history,
        'timestamp': requests.utils.default_headers()
    }
    
    print(f"\n{'='*80}")
    print("✅ ENHANCED SEARCH COMPLETED")
    print(f"{'='*80}")
    
    return result

def extract_building_details(bygning_data, service_username, service_password):
    """Extract detailed building information"""
    building_details = []
    enhed_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/enhed"
    
    for bygning in bygning_data:
        bygning_id = bygning.get("id_lokalId")
        if not bygning_id:
            continue
        
        print(f"  🔍 Checking building ID: ...{bygning_id[-12:]}")
        
        enhed_params = {
            "Bygning": bygning_id,
            "username": service_username,
            "password": service_password
        }
        
        try:
            response_enhed = requests.get(enhed_endpoint, params=enhed_params)
            if response_enhed.status_code == 200:
                enheds_data = response_enhed.json()
                if enheds_data:
                    for unit in enheds_data:
                        area = unit.get('enh027ArealTilBeboelse')
                        rooms = unit.get('enh031AntalVærelser')
                        bathrooms = unit.get('enh065AntalVandskylledeToiletter')
                        
                        unit_detail = {
                            'building_id': bygning_id,
                            'area_sqm': area,
                            'rooms': rooms,
                            'bathrooms': bathrooms,
                            'unit_data': unit
                        }
                        building_details.append(unit_detail)
                        
                        print(f"    ✅ Unit: {area}m², {rooms} rooms, {bathrooms} bathrooms")
        except Exception as e:
            print(f"    ❌ Error fetching unit data: {e}")
    
    return building_details

def get_bfe_number(adgangsadresse_id, service_username, service_password):
    """Get BFE property number"""
    bfe_endpoint = "https://services.datafordeler.dk/DAR/DAR_BFE_Public/1/rest/husnummerTilBygningBfe"
    bfe_params = {
        "husnummerId": adgangsadresse_id,
        "username": service_username,
        "password": service_password
    }
    
    response_bfe = requests.get(bfe_endpoint, params=bfe_params)
    response_bfe.raise_for_status()
    bfe_data = response_bfe.json()
    
    if bfe_data and "jordstykkeList" in bfe_data and bfe_data["jordstykkeList"]:
        return bfe_data["jordstykkeList"][0].get("samletFastEjendom")
    
    return None

def get_sales_history(bfe_nummer, service_username, service_password):
    """Get sales history from Ejerfortegnelsen"""
    ejer_endpoint = "https://services.datafordeler.dk/EJERFORTEGNELSE/Ejerfortegnelsen/1/rest/Handelsoplysning"
    ejer_params = {
        "BFEnr": bfe_nummer,
        "username": service_username,
        "password": service_password
    }
    
    response_ejer = requests.get(ejer_endpoint, params=ejer_params)
    
    if response_ejer.status_code != 200:
        print(f"⚠️ Ejerfortegnelsen error: {response_ejer.status_code} {response_ejer.reason}")
        return []
    
    return response_ejer.json() or []

def get_specific_apartment_data(full_address_string, service_username, service_password):
    """Get data for a SPECIFIC apartment unit"""
    
    print("=" * 80)
    print(f"🏠 SPECIFIC APARTMENT DATA FOR: {full_address_string}")
    print("=" * 80)
    
    # Step 1: Find the exact address
    parser = DanishAddressParser()
    dawa_results, parsed_components = parser.search_address_dawa(full_address_string)
    print(dawa_results)
    if not dawa_results:
        print("❌ Could not find address in DAWA")
        return None
    
    best_match = find_best_address_match(dawa_results, parsed_components)
    if not best_match:
        return None
    
    # Use the specific apartment ID (not adgangsadresseid)
    apartment_id = best_match.get('id')
    adgangsadresse_id = best_match.get('adgangsadresseid')
    
    print(f"✅ Found apartment: {best_match.get('betegnelse', 'Unknown')}")
    print(f"🆔 Specific apartment ID: {apartment_id}")
    print(f"🏠 Building entrance ID: {adgangsadresse_id}")
    
    # Step 2: Get specific apartment data using apartment ID
    print("\n--- Step 2: Getting Specific Apartment Data ---")
    
    apartment_data = get_apartment_unit_data(apartment_id, service_username, service_password)
    
    # Step 3: Also get building-level data for context
    print("\n--- Step 3: Getting Building Context ---")
    
    building_data = get_building_data_by_entrance(adgangsadresse_id, service_username, service_password)
    
    result = {
        'search_query': full_address_string,
        'apartment_id': apartment_id,
        'adgangsadresse_id': adgangsadresse_id,
        'dawa_result': best_match,
        'specific_apartment': apartment_data,
        'building_context': building_data,
        'parsed_address': parsed_components
    }
    
    print(f"\n{'='*80}")
    print("✅ SPECIFIC APARTMENT SEARCH COMPLETED")
    print(f"{'='*80}")
    
    return result

def get_apartment_unit_data(apartment_id, service_username, service_password):
    """Get data for the specific apartment unit using apartment ID"""
    
    print(f"🔍 Fetching data for specific apartment: {apartment_id}")
    
    # Try BBR enhed lookup with the specific apartment ID
    enhed_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/enhed"
    enhed_params = {
        "AdresseIdentificerer": apartment_id,  # Use the correct parameter name
        "username": service_username,
        "password": service_password
    }

    try:
        response = requests.get(enhed_endpoint, params=enhed_params)
        print(response.status_code)
        print(f"📡 BBR enhed response: {response.json()}")

        if response.status_code == 200:
            enhed_data = response.json()
            if enhed_data:
                print(f"✅ Found {len(enhed_data)} unit(s) for this apartment") 
                
                for i, unit in enumerate(enhed_data):
                    area = unit.get('enh027ArealTilBeboelse')
                    rooms = unit.get('enh031AntalVærelser')
                    bathrooms = unit.get('enh065AntalVandskylledeToiletter')
                    floor = unit.get('enh020Etage')
                    
                    print(f"  📊 Unit {i+1}:")
                    print(f"    🏠 Area: {area} m²")
                    print(f"    🚪 Rooms: {rooms}")
                    print(f"    🚿 Bathrooms: {bathrooms}")
                    print(f"    📶 Floor: {floor}")
                
                return enhed_data
            else:
                print("⚠️ No unit data found for this apartment ID")
                return []
        else:
            print(f"❌ BBR enhed error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching apartment data: {e}")
        return []

def get_building_data_by_entrance(adgangsadresse_id, service_username, service_password):
    """Get all units in the building for context"""
    
    print(f"🔍 Fetching building context data: {adgangsadresse_id}")
    
    bygning_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning"
    bygning_params = {
        "Husnummer": adgangsadresse_id,
        "username": service_username,
        "password": service_password
    }
    
    try:
        response = requests.get(bygning_endpoint, params=bygning_params)
        if response.status_code == 200:
            bygning_data = response.json()
            
            if bygning_data:
                print(f"✅ Found {len(bygning_data)} building(s)")
                
                # Get all units in the building
                all_units = []
                for bygning in bygning_data:
                    bygning_id = bygning.get("id_lokalId")
                    if bygning_id:
                        units = get_building_units(bygning_id, service_username, service_password)
                        all_units.extend(units)
                
                print(f"📊 Total units in building: {len(all_units)}")
                return {
                    'buildings': bygning_data,
                    'all_units': all_units,
                    'building_summary': {
                        'total_units': len(all_units),
                        'avg_area': sum(u.get('enh027ArealTilBeboelse', 0) for u in all_units if u.get('enh027ArealTilBeboelse')) / len(all_units) if all_units else 0
                    }
                }
            else:
                print("⚠️ No building data found")
                return {}
        else:
            print(f"❌ Building data error: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"❌ Error fetching building data: {e}")
        return {}

def get_building_units(bygning_id, service_username, service_password):
    """Get all units in a specific building"""
    
    enhed_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/enhed"
    enhed_params = {
        "Bygning": bygning_id,
        "username": service_username,
        "password": service_password
    }
    
    try:
        response = requests.get(enhed_endpoint, params=enhed_params)
        if response.status_code == 200:
            return response.json() or []
        else:
            return []
    except Exception as e:
        print(f"  ❌ Error fetching units for building {bygning_id}: {e}")
        return []

# Test both approaches
if __name__ == '__main__':
    service_user_name = "XEVPPQIYSU"
    service_user_password = "Luffygear3!"
    address_to_search = "sølvgade 3 5 th "  # Specific apartment
    
    print("🆚 COMPARING APARTMENT-SPECIFIC vs BUILDING-WIDE DATA")
    print("=" * 80)
    
    try:
        # Get data for the specific apartment
        specific_result = get_property_data_enhanced(address_to_search, service_user_name, service_user_password)
        
        
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()