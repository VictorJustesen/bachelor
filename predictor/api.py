import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, create_model
from typing import Dict, Any, Optional
import logging
import numpy as np
import xgboost as xgb

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'best_model')
MODEL_NAME = 'finaltest'
MODEL_PKL_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}.pkl')
MODEL_JSON_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}_xgboost.json')
app = FastAPI(redirect_slashes=False)
model_package = None
DynamicPredictionInput = None

def create_feature_mapping():
    """
    Creates a mapping from incoming feature names to model feature names.
    This handles the naming differences between FeatureGenerator and trained model.
    """
    mapping = {}
    
    direct_features = [
        'index', 'prev_købesum', 'Vær.', 'm2', 'byggeaar', 
        'pris_pr_m2_mean_365D_postnummer', 'pris_pr_m2_mean_365D_postnummer_btype',
        'pris_pr_m2_prev', 'pris_pr_m2_mean_postummer_prev', 
        'pris_pr_m2_mean_postnummer_btype_prev', 'days_since_last_sale',
        'num_of_5_neighbors', 'mean_of_5_neighbors_pris_pr_m2',
        'num_of_5_samebtype_neighbors', 'mean_of_5_samebtype_neighbors_pris_pr_m2',
        'historical_premium_vs_postnummer', 'historical_premium_vs_postnummer_pct',
        'historical_premium_vs_postnummer_btype', 'historical_premium_vs_postnummer_btype_pct',
        'mean_of_5_neighbors_pris', 'mean_of_5_samebtype_neighbors_pris',
        'postnummer_pris_estimate', 'postnummer_pris_premium_adjusted',
        'postnummer_btype_pris_estimate', 'postnummer_btype_pris_premium_adjusted',

    ]
    
    for feature in direct_features:
        mapping[feature] = feature
    
    building_types = ['Ejerlejlighed', 'Villa', 'Rækkehus', 'Fritidshus', 'Landejendom']
    for btype in building_types:
        mapping[f'btype_{btype}'] = f'btype_{btype}'
        mapping[f'btype.{btype}'] = f'btype_{btype}'
    
    area_mappings = {
        'område_Bornholm': 'omr_de_Bornholm',
        'område_Fyn og øer': 'omr_de_Fyn_og__er',
        'område_Hovedstaden (København)': 'omr_de_Hovedstaden__K_benhavn',
        'område_Nordjylland': 'omr_de_Nordjylland',
        'område_Nordsjælland': 'omr_de_Nordsj_lland',
        'område_Sydjylland': 'omr_de_Sydjylland',
        'område_Øst- og Midtjylland': 'omr_de__st__og_Midtjylland',
        'område_Hovedstaden_København' :'omr_de_Hovedstaden__K_benhavn',
        'btype_Rækkehus' : 'btype_R_kkehus',
        
         'prev_købesum': 'prev_k_besum', 
        'Vær.': 'V_r_',  
        
    }
    
    for incoming, model in area_mappings.items():
        mapping[incoming] = model
    
    return mapping

@app.on_event("startup")
def load_model():
    """
    Load the model package from disk when the application starts.
    """
    global model_package, DynamicPredictionInput
    
    if not os.path.exists(MODEL_PKL_PATH):
        raise RuntimeError(f"Model PKL file not found at {MODEL_PKL_PATH}")
    
    print(f"Loading model package from: {MODEL_PKL_PATH}")
    model_package = joblib.load(MODEL_PKL_PATH)
    print("Model package loaded successfully.")

    if os.path.exists(MODEL_JSON_PATH):
        print(f"Loading XGBoost weights from: {MODEL_JSON_PATH}")
        xgb_model = xgb.XGBRegressor()
        xgb_model.load_model(MODEL_JSON_PATH)
        model_package['model'] = xgb_model
        print("XGBoost weights loaded successfully.")
    else:
        print(f"Warning: XGBoost JSON weights not found at {MODEL_JSON_PATH}")

    if model_package and 'feature_columns' in model_package:
        fields = {feature: (Optional[float], 0.0) for feature in model_package['feature_columns']}
        DynamicPredictionInput = create_model('PredictionInput', **fields)
        print(f"Created input validation for {len(fields)} features")
        
        feature_columns = model_package['feature_columns']
        print(f"Building type features: {[f for f in feature_columns if f.startswith('btype_')]}")
        print(f"Area features: {[f for f in feature_columns if f.startswith('omr_de_')]}")
    else:
        raise ValueError("Could not find 'feature_columns' in the loaded model package.")

@app.get("/")
def read_root():
    return {"status": "Predictor API is running"}

@app.get("/model-info/")
def get_model_info():
    if not model_package:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    
    feature_columns = model_package.get('feature_columns', [])
    
    return {
        "model_type": str(type(model_package['model']).__name__),
        "feature_columns": feature_columns,
        "target_column": model_package.get('target_col', 'Unknown'),
        "num_features": len(feature_columns),
        "building_types": [f for f in feature_columns if f.startswith('btype_')],
        "areas": [f for f in feature_columns if f.startswith('omr_de_')]
    }

@app.post("/predict/")
async def predict(request: Request):
    """
    Receives property data and returns a prediction using XGBoost model.
    """
    if not model_package or not DynamicPredictionInput:
        raise HTTPException(status_code=503, detail="Model is not loaded or initialized properly")

    try:
        raw_data = await request.json()
        print(f"--- Prediction request for: {raw_data.get('address', 'Unknown')} ---")

        model = model_package['model']
        scaler = model_package.get('scaler')
        feature_columns = model_package['feature_columns']
        
        feature_mapping = create_feature_mapping()
        
        input_data_dict = {feature: np.nan for feature in feature_columns}
        
        mapped_features = 0
        translation_log = []
        unmapped_incoming = []
        mapped_model_features = set()
        
        for incoming_key, value in raw_data.items():
            if value is None:
                continue
                
            mapped = False
            
            if incoming_key in feature_mapping:
                model_key = feature_mapping[incoming_key]
                if model_key in feature_columns:
                    try:
                        input_data_dict[model_key] = float(value)
                        mapped_features += 1
                        mapped_model_features.add(model_key)
                        translation_log.append(f"{incoming_key} -> {model_key} = {value}")
                        mapped = True
                    except (ValueError, TypeError):
                        input_data_dict[model_key] = np.nan
                        mapped_model_features.add(model_key)
                        translation_log.append(f"{incoming_key} -> {model_key} = np.nan (conversion error)")
                        mapped = True
            elif incoming_key in feature_columns:
                try:
                    input_data_dict[incoming_key] = float(value)
                    mapped_features += 1
                    mapped_model_features.add(incoming_key)
                    translation_log.append(f"{incoming_key} = {value} (direct)")
                    mapped = True
                except (ValueError, TypeError):
                    input_data_dict[incoming_key] = np.nan
                    mapped_model_features.add(incoming_key)
                    translation_log.append(f"{incoming_key} = np.nan (direct, conversion error)")
                    mapped = True
            
            if not mapped:
                unmapped_incoming.append(f"{incoming_key} = {value}")
        
        unmapped_model_features = [f for f in feature_columns if f not in mapped_model_features]
        
        print(f"Mapped {mapped_features} features out of {len(feature_columns)} total")
        
        if mapped_features > 0:
            print(f"\n Feature mappings (showing first 15):")
            for log_entry in translation_log[:15]:
                print(f"   {log_entry}")
            if len(translation_log) > 15:
                print(f"   and {len(translation_log) - 15} more mappings")
        
        if unmapped_incoming:
            print(f"\n UNMAPPED INCOMING FEATURES ({len(unmapped_incoming)}):")
            for unmapped in unmapped_incoming:  # Show first 20
                print(f"   {unmapped}")
            if len(unmapped_incoming) > 20:
                print(f"   and {len(unmapped_incoming) - 20} more unmapped incoming features")
        
        if unmapped_model_features:
            print(f"\n  MODEL FEATURES SET TO 0.0 ({len(unmapped_model_features)}):")
            building_types = [f for f in unmapped_model_features if f.startswith('btype_')]
            areas = [f for f in unmapped_model_features if f.startswith('omr_de_')]
            other_features = [f for f in unmapped_model_features if not f.startswith('btype_') and not f.startswith('omr_de_')]
            
            if building_types:
                print(f"   Building types (0/1): {building_types}")
            if areas:
                print(f"   Areas (0/1): {areas}")
            if other_features[:10]:  # Show first 10 other features
                print(f"   Other features: {other_features[:10]}")
                if len(other_features) > 10:
                    print(f"   ... and {len(other_features) - 10} more other features")
        
        input_df = pd.DataFrame([input_data_dict], columns=feature_columns)
        
        non_zero_features = {col: val for col, val in input_data_dict.items()}
        if non_zero_features:
            print(f"\nNON-ZERO FEATURES ({len(non_zero_features)}):")
            for feature, value in list(non_zero_features.items()):
                print(f"   {feature} = {value}")
            if len(non_zero_features) > 10:
                print(f"   ... and {len(non_zero_features) - 10} more non zero features")
        
        if scaler is not None:
            print("Applying scaler transformation")
            scaled_data = scaler.transform(input_df)
            scaled_data = np.nan_to_num(scaled_data, nan=0.0, posinf=0.0, neginf=0.0)
            input_for_prediction = pd.DataFrame(scaled_data, columns=input_df.columns)
        else:
            print("No scaler found, using raw features")
            input_for_prediction = input_df.fillna(0)

        print("Making prediction")
        prediction = model.predict(input_for_prediction)
        predicted_price = float(prediction[0])
        
        predicted_price = max(100000, predicted_price)
        
        print(f" Prediction: {predicted_price:,.0f} DKK")
        
        return {
            "prediction": predicted_price,
            "target_column": model_package.get('target_col', 'købesum'),
            "model_type": str(type(model).__name__),
            "features_used": mapped_features,
            "total_features": len(feature_columns),
            "unmapped_incoming": len(unmapped_incoming),
            "unmapped_model_features": len(unmapped_model_features)
        }

    except Exception as e:
        print(f" Prediction error: {str(e)}")
        logging.error("An error occurred during prediction", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/health/")
def health_check():
    """Health check endpoint"""
    if not model_package:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "features_available": len(model_package.get('feature_columns', [])),
        "model_type": str(type(model_package['model']).__name__)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)