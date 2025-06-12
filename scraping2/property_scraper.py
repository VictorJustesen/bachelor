import requests
import re

def parse_danish_address(address_string):
    cleaned = address_string.strip().replace(',', ' ').replace('.', '').replace("denmark", "")
    cleaned = ' '.join(cleaned.split())
    
    result = {
        'vejnavn': None,
        'husnr': None,
        'etage': None,
        'dør': None,
        'postnr': None,
        'city': None
    }
    
    postal_code_pattern = r'\b\d{4}\b'
    postal_matches = list(re.finditer(postal_code_pattern, cleaned))
    
    if postal_matches:
        postal_match = postal_matches[-1]
        result['postnr'] = postal_match.group()
        postal_index = postal_match.start()
        
        city_part = cleaned[postal_match.end():].strip()
        if city_part:
            result['city'] = city_part
        
        address_part = cleaned[:postal_index].strip()
    else:
        address_part = cleaned
    
    address_parts = address_part.split()
    if not address_parts:
        return result
    
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
    
    if remaining_parts:
        floor_patterns = [r'^(st|kl|k[2-9])$', r'^\d{1,2}$']
        door_patterns = [r'^(tv|th)$', r'^\d{1,4}$', r'^[a-z]$', r'^\d+-\d+$', r'^\d+[a-z]$']
        
        for part in remaining_parts:
            part_lower = part.lower()
            if not result['etage'] and any(re.match(pattern, part_lower) for pattern in floor_patterns):
                result['etage'] = part_lower
            elif not result['dør'] and any(re.match(pattern, part_lower) for pattern in door_patterns):
                result['dör'] = part_lower
    
    return result

def search_dawa_address(address_string):
    dawa_url = "https://api.dataforsyningen.dk/adresser"
    parsed = parse_danish_address(address_string)
    
    params = {'struktur': 'mini'}
    if parsed['vejnavn']:
        params['vejnavn'] = parsed['vejnavn']
    if parsed['husnr']:
        params['husnr'] = parsed['husnr']
    if parsed['etage']:
        params['etage'] = parsed['etage']
    if parsed['dør']:
        params['dör'] = parsed['dör']
    if parsed['postnr']:
        params['postnr'] = parsed['postnr']
    
    try:
        response = requests.get(dawa_url, params=params)
        response.raise_for_status()
        results = response.json()
        if results:
            return results, parsed
    except:
        pass
    
    fallback_params = {'q': address_string, 'struktur': 'mini'}
    try:
        response = requests.get(dawa_url, params=fallback_params)
        response.raise_for_status()
        return response.json(), parsed
    except:
        return [], parsed

def find_best_address_match(dawa_results):
    if not dawa_results:
        return None
    
    for result in dawa_results:
        if 'adgangsadresseid' in result and result['adgangsadresseid']:
            return result
        elif 'adgangsadresse' in result and isinstance(result['adgangsadresse'], dict):
            if 'id' in result['adgangsadresse']:
                return result
    
    return dawa_results[0] if dawa_results else None

def get_apartment_data(apartment_id, username, password):
    enhed_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/enhed"
    params = {
        "AdresseIdentificerer": apartment_id,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.get(enhed_endpoint, params=params)
        if response.status_code == 200:
            return response.json() or []
    except:
        pass
    return []

def get_building_data(adgangsadresse_id, username, password):
    bygning_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning"
    params = {
        "Husnummer": adgangsadresse_id,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.get(bygning_endpoint, params=params)
        if response.status_code == 200:
            return response.json() or []
    except:
        pass
    return []

def get_bfe_number(adgangsadresse_id, username, password):
    bfe_endpoint = "https://services.datafordeler.dk/DAR/DAR_BFE_Public/1/rest/husnummerTilBygningBfe"
    params = {
        "husnummerId": adgangsadresse_id,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.get(bfe_endpoint, params=params)
        response.raise_for_status()
        bfe_data = response.json()
        
        if bfe_data and "jordstykkeList" in bfe_data and bfe_data["jordstykkeList"]:
            return bfe_data["jordstykkeList"][0].get("samletFastEjendom")
    except:
        pass
    return None

def get_sales_history(bfe_nummer, username, password):
    ejer_endpoint = "https://services.datafordeler.dk/EJERFORTEGNELSE/Ejerfortegnelsen/1/rest/Handelsoplysning"
    params = {
        "BFEnr": bfe_nummer,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.get(ejer_endpoint, params=params)
        if response.status_code == 200:
            return response.json() or []
    except:
        pass
    return []

def scrape_property_data(address_string, username, password):
    dawa_results, parsed = search_dawa_address(address_string)
    if not dawa_results:
        return None
    
    best_match = find_best_address_match(dawa_results)
    if not best_match:
        return None
    
    apartment_id = best_match.get('id')
    adgangsadresse_id = best_match.get('adgangsadresseid')
    
    if not adgangsadresse_id and 'adgangsadresse' in best_match:
        adgangsadresse_id = best_match['adgangsadresse'].get('id')
    
    if not adgangsadresse_id:
        return None
    
    apartment_data = get_apartment_data(apartment_id, username, password)
    building_data = get_building_data(adgangsadresse_id, username, password)
    bfe_number = get_bfe_number(adgangsadresse_id, username, password)
    sales_history = get_sales_history(bfe_number, username, password) if bfe_number else []
    
    return {
        'address': best_match.get('betegnelse', best_match.get('adressebetegnelse')),
        'apartment_id': apartment_id,
        'adgangsadresse_id': adgangsadresse_id,
        'apartment_data': apartment_data,
        'building_data': building_data,
        'bfe_number': bfe_number,
        'sales_history': sales_history,
        'coordinates': [best_match.get('x'), best_match.get('y')]
    }