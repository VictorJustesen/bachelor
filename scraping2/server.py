import os
import sys
import random
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

sys.path.append(os.path.dirname(__file__))
from property_scraper import scrape_property_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = int(os.environ.get('PORT', 9000))

SERVICE_USERNAME = "XEVPPQIYSU"
SERVICE_PASSWORD = "Luffygear3!"

class ScrapeBuildingRequest(BaseModel):
    address: str

class ScrapeHistoryRequest(BaseModel):
    address: str
    zip: str

@app.post('/scrape/building-info')
async def scrape_building_info(req: ScrapeBuildingRequest):
    
    address = req.address
    print(f'Scraping building info for: {address}')
    print("hey")
    
    try:
        python_result = call_property_scraper(address)
        
        if python_result.get('success') and python_result.get('data'):
            data = python_result['data']
            
            return {
                'address': data.get('address'),
                'sqm': extract_sqm_from_data(data.get('apartment_data')),
                'rooms': extract_rooms_from_data(data.get('apartment_data')),
                'year': extract_year_from_data(data.get('building_data')),
                'zip': extract_zip_from_address(data.get('address')),
                'city': extract_city_from_address(data.get('address')),
                'buildingType': extract_building_type(data.get('building_data')),
                'coordinates': data.get('coordinates'),
                'salesHistory': data.get('sales_history'),
                'source': 'danish_property_scraper',
                'apartment_id': data.get('apartment_id'),
                'adgangsadresse_id': data.get('adgangsadresse_id'),
                'bfe_number': data.get('bfe_number')
            }
        else:
            print('Python scraper returned no data, using mock data')
            return generate_mock_building_data(address)
            
    except Exception as error:
        print(f'Property scraping failed: {error}')
        return generate_mock_building_data(address)

@app.post('/scrape/property-history')
async def scrape_property_history(req: ScrapeHistoryRequest):
    address = req.address
    zip_code = req.zip
    
    try:
        print(f'Scraping property history for: {address}, {zip_code}')
        
        python_result = call_property_scraper(address)
        
        if python_result.get('success') and python_result.get('data'):
            data = python_result['data']
            
            return {
                'address': data.get('address'),
                'zip': extract_zip_from_address(data.get('address')),
                'salesHistory': data.get('sales_history', []),
                'source': 'danish_property_scraper'
            }
        else:
            return {
                'address': address,
                'zip': zip_code,
                'salesHistory': [
                    {
                        'date': "2023-01-15",
                        'price': random.randint(1000000, 3000000)
                    }
                ],
                'source': 'mock_fallback'
            }
            
    except Exception as error:
        print(f'Property history scraping failed: {error}')
        raise HTTPException(status_code=500, detail='Failed to get property history')

def call_property_scraper(address):
    try:
        result = scrape_property_data(address, SERVICE_USERNAME, SERVICE_PASSWORD)
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def extract_sqm_from_data(apartment_data):
    if not apartment_data or not isinstance(apartment_data, list):
        return None
    
    for apartment in apartment_data:
        if apartment.get('enh027ArealTilBeboelse'):
            return float(apartment['enh027ArealTilBeboelse'])
        if apartment.get('enh026EnhedensSamledeAreal'):
            return float(apartment['enh026EnhedensSamledeAreal'])
    return None

def extract_rooms_from_data(apartment_data):
    if not apartment_data or not isinstance(apartment_data, list):
        return None
    
    for apartment in apartment_data:
        if apartment.get('enh031AntalVærelser'):
            return int(apartment['enh031AntalVærelser'])
    return None

def extract_year_from_data(building_data):
    if not building_data or not isinstance(building_data, list):
        return None
    
    for building in building_data:
        if building.get('byg026Opførelsesår'):
            return int(building['byg026Opførelsesår'])
    return None

def extract_zip_from_address(address):
    if not address:
        return None
    zip_match = re.search(r'\b\d{4}\b', address)
    return zip_match.group(0) if zip_match else None

def extract_city_from_address(address):
    if not address:
        return None
    parts = address.split(' ')
    return parts[-1] if parts else None

def extract_building_type(building_data):
    if not building_data or not isinstance(building_data, list):
        return 'Unknown'
    
    for building in building_data:
        if building.get('byg021BygningensAnvendelse'):
            code = building['byg021BygningensAnvendelse']
            if code == "120":
                return "Residential Building"
            if code == "920":
                return "Auxiliary Building"
            return f"Building Type {code}"
    return 'Residential Building'

def generate_mock_building_data(address):
    return {
        'address': address,
        'sqm': random.randint(50, 250),
        'rooms': random.randint(2, 8),
        'year': random.randint(1970, 2020),
        'zip': '1000',
        'city': 'København',
        'buildingType': 'Boligbyggeri',
        'coordinates': [55.6761, 12.5683],
        'salesHistory': [],
        'source': 'mock_data'
    }

if __name__ == '__main__':
    print(f'Scraping server running on port {PORT}')
    uvicorn.run(app, host='0.0.0.0', port=PORT)