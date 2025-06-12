import re
import requests
from typing import Dict, Optional, Tuple

class DanishAddressParser:
    """
    Parses Danish addresses and searches using DAWA API with proper parameters
    
    Danish address structure:
    - Street name (first part)
    - House number (number after street name)
    - Floor/etage (optional: st, 1-99, kl, k2-k9)
    - Door/side (optional: number, tv, th, or combination)
    - Postal code (4 digits)
    - City name (after postal code)
    """
    
    def __init__(self):
        self.dawa_base_url = "https://api.dataforsyningen.dk/adresser"
    
    def parse_danish_address(self, address_string: str) -> Dict[str, Optional[str]]:
        """
        Parse a Danish address string into components
        
        Examples:
        - "Store Kongensgade 63A 1264 København K"
        - "Vesterbrogade 22 st tv 1620 København V" 
        - "Nørrebrogade 45 2 th 2200 København N"
        - "Hovedgaden 12 8000 Aarhus C"
        """
        
        # Clean up the address
        cleaned = address_string.strip()
        parts = cleaned.split()
        
        result = {
            'vejnavn': None,
            'husnr': None,
            'etage': None,
            'dør': None,
            'postnr': None,
            'city': None,
            'original': address_string
        }
        
        # Find postal code (4 digits)
        postal_code_pattern = r'\b\d{4}\b'
        postal_matches = list(re.finditer(postal_code_pattern, cleaned))
        
        if postal_matches:
            # Take the last 4-digit number as postal code
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
            # No postal code found, treat entire string as address
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
                # This is the house number
                result['husnr'] = part
                house_number_found = True
                # Everything after house number might be floor/door
                remaining_parts = address_parts[i+1:]
                break
            else:
                # Part of street name
                street_name_parts.append(part)
        
        if street_name_parts:
            result['vejnavn'] = ' '.join(street_name_parts)
        
        # Parse remaining parts for floor and door
        if remaining_parts:
            # Common floor indicators
            floor_patterns = [
                r'^(st|kl|k[2-9])$',  # st, kl, k2-k9
                r'^\d{1,2}$'          # 1-99
            ]
            
            # Common door indicators  
            door_patterns = [
                r'^(tv|th)$',         # tv, th
                r'^\d{1,4}$',         # numbers
                r'^[a-z]$',           # single letters
                r'^\d+-\d+$',         # ranges like 1-2
                r'^\d+[a-z]$'         # number + letter
            ]
            
            i = 0
            while i < len(remaining_parts):
                part = remaining_parts[i].lower()
                
                # Check if it's a floor indicator
                if not result['etage'] and any(re.match(pattern, part) for pattern in floor_patterns):
                    result['etage'] = part
                # Check if it's a door indicator
                elif not result['dør'] and any(re.match(pattern, part) for pattern in door_patterns):
                    result['dør'] = part
                
                i += 1
        
        return result
    
    def search_address_dawa(self, address_string: str, use_autocomplete: bool = False) -> list:
        """
        Search for address using DAWA API with parsed components
        """
        
        # First try with parsed components
        parsed = self.parse_danish_address(address_string)
        
        params = {
            'struktur': 'mini'  # Better performance
        }
        
        # Add parsed components as specific parameters
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
            print(f"🔍 Searching with parsed components: {params}")
            response = requests.get(self.dawa_base_url, params=params)
            response.raise_for_status()
            results = response.json()
            
            if results:
                print(f"✅ Found {len(results)} results with component search")
                return results
            
        except Exception as e:
            print(f"⚠️ Component search failed: {e}")
        
        # Fallback to general text search
        fallback_params = {
            'q': address_string,
            'struktur': 'mini'
        }
        
        if use_autocomplete:
            fallback_params['autocomplete'] = '1'
        
        try:
            print(f"🔍 Fallback search with q parameter")
            response = requests.get(self.dawa_base_url, params=fallback_params)
            response.raise_for_status()
            results = response.json()
            
            print(f"✅ Found {len(results)} results with fallback search")
            return results
            
        except Exception as e:
            print(f"❌ All searches failed: {e}")
            return []
    
    def get_best_address_match(self, address_string: str) -> Optional[Dict]:
        """
        Get the best matching address from DAWA
        """
        results = self.search_address_dawa(address_string)
        
        if not results:
            return None
        
        # Return the first result (DAWA usually returns best matches first)
        best_match = results[0]
        
        # Add our parsed components for reference
        parsed = self.parse_danish_address(address_string)
        best_match['parsed_components'] = parsed
        
        return best_match
