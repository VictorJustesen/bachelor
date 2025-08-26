import os
import sys
import random
import re
import json
import numpy as np
import pandas as pd  # ADD THIS LINE


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# --- NEW: Import the FeatureGenerator class ---
from FeatureGenerator import FeatureGenerator

app = FastAPI()

# --- NEW: A global variable to hold the feature service instance ---
# We will initialize this at startup to avoid reloading the data on every request.
feature_service: FeatureGenerator = None

# --- NEW: Use FastAPI's startup event to load the model ---
@app.on_event("startup")
def load_feature_generator():
    """
    This function runs when the server starts. It loads the data and 
    initializes the FeatureGenerator, making it ready to handle requests.
    """
    global feature_service
    
    # Make the data path configurable via an environment variable
    data_path = os.environ.get("DATA_FILE_PATH", "dataexplor/cleaned_data_harshertesttest4.csv")
    
    if not os.path.exists(data_path):
        # If the data isn't found, the server can't start.
        raise FileNotFoundError(f"CRITICAL: Data file not found at '{data_path}'. The server cannot start.")
        
    print("Initializing FeatureGenerator for the service...")
    feature_service = FeatureGenerator(data_path=data_path)
    # The "Initialization complete. Service is ready." message will print here.


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

class ScrapeHistoryRequest(BaseModel):
    address: str
    zip: str


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
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


# --- MODIFIED: The endpoint now uses the feature generator ---
@app.post('/scrape/building-info')
async def scrape_building_info(req: ScrapeBuildingRequest):
    address = req.address
    print(f'Generating features for: {address}')
    
    if feature_service is None:
        print('FeatureGenerator not available, using mock data')
        return generate_mock_building_data(address)
    
    try:
        features = feature_service.generate_for_address(address)
        
        if features:
            features = convert_numpy_types(features)
            
            # Simply rename the fields your frontend expects
            features['address'] = features.get('full_address', address)
            features['sqm'] = features.get('m2')
            features['rooms'] = features.get('Vær.')  # or however rooms are stored
            features['year'] = features.get('byggeaar')
            features['zip'] = str(features.get('postnummer', ''))
            features['city'] = features.get('by')
            features['buildingType'] = features.get('btype')
            
            # Handle coordinates
            if features.get('y') and features.get('x'):
                features['coordinates'] = [features.get('y'), features.get('x')]
            else:
                features['coordinates'] = None

            building_type = features.get('btype', '')
            building_types = ['Villa', 'Ejerlejlighed', 'Rækkehus', 'Fritidshus', 'Landejendom']
            
            for btype in building_types:
                features[f'btype_{btype}'] = 1 if building_type == btype else 0
                
            features['source'] = 'feature_generator_service'
            
            # Return the entire features dict (now with renamed fields)
            return features
            
        else:
            print('Feature generation failed, using mock data')
            return generate_mock_building_data(address)
            
    except Exception as error:
        print(f'Feature generation error: {error}')
        return generate_mock_building_data(address)


# This endpoint is unchanged, but you could also integrate it if needed
@app.post('/scrape/property-history')
async def scrape_property_history(req: ScrapeHistoryRequest):
    address = req.address
    zip_code = req.zip
    print(f'Getting property history for: {address}')

    try:
        # Use the new method from our initialized feature_service
        history = feature_service.get_sales_history_for_address(address)
        
        # The method returns a list if successful (even an empty one for no sales) 
        # or None if the address lookup itself failed.
        if history is not None:
            return {
                'address': address,
                'zip': zip_code,
                'salesHistory': history, # This will be the list from our new method
                'source': 'feature_generator_dataset'
            }
        else:
            # If history is None, it means the address could not be found by DAWA.
            raise HTTPException(status_code=404, detail="Address not found or could not be identified.")

    except Exception as error:
        print(f'Property history lookup failed: {error}')
        # This will catch any unexpected errors during the process
        raise HTTPException(status_code=500, detail='Failed to get property history')

# Mock data function is unchanged
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
    # You still run the server the same way
    print(f'Scraping and feature server running on port {PORT}')
    uvicorn.run(app, host='0.0.0.0', port=PORT)