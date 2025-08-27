import os
import sys
import random
import re
import json
import numpy as np
import pandas as pd
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from FeatureGenerator import FeatureGenerator

app = FastAPI()

feature_service: FeatureGenerator = None

@app.on_event("startup")
def load_feature_generator():
    global feature_service
    
    data_path = os.environ.get("DATA_FILE_PATH", "dataexplor/cleaned_data_harshertesttest4.csv")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"CRITICAL: Data file not found at '{data_path}'. The server cannot start.")
        
    print("Initializing FeatureGenerator for the service...")
    feature_service = FeatureGenerator(data_path=data_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = int(os.environ.get('PORT', 9000))

class ScrapeBuildingRequest(BaseModel):
    address: str
    sqm: Optional[float] = None
    rooms: Optional[int] = None
    zip: Optional[str] = None
    buildingType: Optional[str] = None

class ScrapeHistoryRequest(BaseModel):
    address: str
    zip: str


def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj) if 'pd' in globals() else str(obj) == 'nan':
        return None
    else:
        return obj

@app.post('/scrape/building-info')
async def scrape_building_info(req: ScrapeBuildingRequest):
    address = req.address
    print(f'Generating features for: {address}')
    
    if feature_service is None:
        print('FeatureGenerator not available, using mock data')
        return generate_mock_building_data(address)
    
    try:
        overrides = {
            "m2": req.sqm,
            "Vær.": req.rooms,
            "postnummer": req.zip,
            "btype": req.buildingType
        }
        
        cleaned_overrides = {k: v for k, v in overrides.items() if v is not None}

        features = feature_service.generate_for_address(address, overrides=cleaned_overrides)
        
        if features:
            features = convert_numpy_types(features)
            
            features['address'] = features.get('full_address', address)
            features['sqm'] = features.get('m2')
            features['rooms'] = features.get('Vær.')
            features['year'] = features.get('byggeaar')
            features['zip'] = str(features.get('postnummer', ''))
            features['city'] = features.get('by')
            features['buildingType'] = features.get('btype')
            
            if features.get('y') and features.get('x'):
                features['coordinates'] = [features.get('y'), features.get('x')]
            else:
                features['coordinates'] = None

            building_type = features.get('btype', '')
            building_types = ['Villa', 'Ejerlejlighed', 'Rækkehus', 'Fritidshus', 'Landejendom']
            
            for btype in building_types:
                features[f'btype_{btype}'] = 1 if building_type == btype else 0
                
            features['source'] = 'feature_generator_service'
            
            return features
            
        else:
            print('Feature generation failed, using mock data')
            return generate_mock_building_data(address)
            
    except Exception as error:
        print(f'Feature generation error: {error}')
        return generate_mock_building_data(address)

@app.post('/scrape/property-history')
async def scrape_property_history(req: ScrapeHistoryRequest):
    address = req.address
    zip_code = req.zip
    print(f'Getting property history for: {address}')

    try:
        history = feature_service.get_sales_history_for_address(address)
        
        if history is not None:
            return {
                'address': address,
                'zip': zip_code,
                'salesHistory': history,
                'source': 'feature_generator_dataset'
            }
        else:
            raise HTTPException(status_code=404, detail="Address not found or could not be identified.")

    except Exception as error:
        print(f'Property history lookup failed: {error}')
        raise HTTPException(status_code=500, detail='Failed to get property history')

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
    print(f'Scraping and feature server running on port {PORT}')
    uvicorn.run(app, host='0.0.0.0', port=PORT)