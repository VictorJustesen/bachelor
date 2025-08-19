import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, create_model
from typing import Dict, Any, Optional
import logging
import numpy as np
import xgboost as xgb  # ADD THIS IMPORT

# --- Configuration ---
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'best_model')
MODEL_NAME = 'finaltest'
MODEL_PKL_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}.pkl')
MODEL_JSON_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}_xgboost.json')

# --- FastAPI App ---
app = FastAPI(redirect_slashes=False)
model_package = None

# --- Pydantic Model for Input Validation ---
DynamicPredictionInput = None

@app.on_event("startup")
def load_model():
    """
    Load the model package from disk when the application starts.
    Handles both PKL metadata and JSON weights for XGBoost.
    """
    global model_package, DynamicPredictionInput
    
    # Load the PKL file with metadata, scaler, features, etc.
    if not os.path.exists(MODEL_PKL_PATH):
        raise RuntimeError(f"Model PKL file not found at {MODEL_PKL_PATH}")
    
    print(f"Loading model package from: {MODEL_PKL_PATH}")
    model_package = joblib.load(MODEL_PKL_PATH)
    print("Model package loaded successfully.")

    # Load the XGBoost JSON weights if they exist
    if os.path.exists(MODEL_JSON_PATH):
        print(f"Loading XGBoost weights from: {MODEL_JSON_PATH}")
        
        # Create a new XGBoost model and load the weights
        xgb_model = xgb.XGBRegressor()
        xgb_model.load_model(MODEL_JSON_PATH)
        
        # Replace the model in the package with the properly loaded one
        model_package['model'] = xgb_model
        print("XGBoost weights loaded successfully.")
    else:
        print(f"Warning: XGBoost JSON weights not found at {MODEL_JSON_PATH}")
        print("Using model from PKL file (may not have proper weights)")

    # Create dynamic input validation
    if model_package and 'feature_columns' in model_package:
        fields = {feature: (Optional[float], 0.0) for feature in model_package['feature_columns']}
        DynamicPredictionInput = create_model('PredictionInput', **fields)
        print(f"Created input validation for {len(fields)} features")
        
        # Debug: Show some sample feature names
        feature_columns = model_package['feature_columns']
        print(f"Sample features: {feature_columns[:5]}...")
        print(f"Building type features: {[f for f in feature_columns if 'btype_' in f]}")
        print(f"Area features: {[f for f in feature_columns if 'område_' in f]}")
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
        "model_metadata": model_package.get('model_metadata', {}),
        "num_features": len(feature_columns),
        "sample_features": feature_columns[:10],  # Show first 10 features
        "building_types": [f for f in feature_columns if 'btype_' in f],
        "areas": [f for f in feature_columns if 'område_' in f]
    }

@app.post("/predict/")
async def predict(request: Request):
    """
    Receives property data and returns a prediction using XGBoost model.
    """
    if not model_package or not DynamicPredictionInput:
        raise HTTPException(status_code=503, detail="Model is not loaded or initialized properly")

    try:
        # Get the raw JSON data
        raw_data = await request.json()
        print(f"--- Received prediction request for address: {raw_data.get('address', 'Unknown')} ---")
        print(f"Raw data keys: {list(raw_data.keys())}")

        model = model_package['model']
        scaler = model_package.get('scaler')
        feature_columns = model_package['feature_columns']

        print(f"\n📋 MODEL EXPECTS THESE FEATURES:")
        for i, feature in enumerate(feature_columns):  # First 15
            print(f"   {i+1:2d}. {feature}")
        if len(feature_columns) > 15:
            print(f"   ... and {len(feature_columns) - 15} more")
        
        # Show what data we received
        print(f"\n📥 RECEIVED DATA KEYS:")
        received_keys = list(raw_data.keys())
        for i, key in enumerate(received_keys):  # First 15
            print(f"   {i+1:2d}. {key} = {raw_data[key]}")
        if len(received_keys) > 15:
            print(f"   ... and {len(received_keys) - 15} more")
        
        # Initialize all features to 0
        input_data_dict = {feature: 0.0 for feature in feature_columns}
        
        # Map incoming data to model features
        mapped_features = 0
        for feature in feature_columns:
            if feature in raw_data and raw_data[feature] is not None:
                try:
                    input_data_dict[feature] = float(raw_data[feature])
                    mapped_features += 1
                except (ValueError, TypeError):
                    input_data_dict[feature] = 0.0
        
        print(f"Mapped {mapped_features} features out of {len(feature_columns)} total")
        
        # Create DataFrame with correct column order
        input_df = pd.DataFrame([input_data_dict], columns=feature_columns)
        print(f"\n📋 INPUT DATAFRAME SHAPE: {input_df.shape}")
        
        # Show a sample of the DataFrame (first 10 columns)
        print(f"\n📊 SAMPLE OF INPUT DATA (first 10 features):")
        print("-" * 80)
        sample_df = input_df
        print(sample_df.to_string(index=False, float_format='{:.3f}'.format))
        # Apply scaling if available
        if scaler is not None:
            print("Applying scaler transformation...")
            scaled_data = scaler.transform(input_df)
            scaled_data = np.nan_to_num(scaled_data, nan=0.0, posinf=0.0, neginf=0.0)
            input_for_prediction = pd.DataFrame(scaled_data, columns=input_df.columns)
        else:
            print("No scaler found, using raw features")
            input_for_prediction = input_df.fillna(0)

        # Make prediction
        print("Making prediction...")
        prediction = model.predict(input_for_prediction[])
        predicted_price = float(prediction[0])
        
        # Ensure reasonable bounds
        predicted_price = max(100000, predicted_price)  # Minimum 100k DKK
        
        print(f"✅ Prediction: {predicted_price:,.0f} DKK")
        
        return {
            "prediction": predicted_price,
            "target_column": model_package.get('target_col', 'købesum'),
            "model_type": str(type(model).__name__),
            "features_used": mapped_features,
            "total_features": len(feature_columns)
        }

    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
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