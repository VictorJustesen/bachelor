import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, create_model
from typing import Dict, Any, Optional
import logging
import numpy as np

# --- Configuration ---
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'best_model')
MODEL_NAME = 'simple_linear_regression'
MODEL_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}.pkl')

# --- FastAPI App ---
app = FastAPI(redirect_slashes=False)
model_package = None

# --- Pydantic Model for Input Validation ---
DynamicPredictionInput = None

@app.on_event("startup")
def load_model():
    """
    Load the model package from disk when the application starts.
    """
    global model_package, DynamicPredictionInput
    
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    
    print(f"Loading model from: {MODEL_PATH}")
    model_package = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")

    if model_package and 'feature_columns' in model_package:
        fields = {feature: (Optional[float], 0.0) for feature in model_package['feature_columns']}
        DynamicPredictionInput = create_model('PredictionInput', **fields)
        print(f"Created input validation for {len(fields)} features")
    else:
        raise ValueError("Could not find 'feature_columns' in the loaded model package.")

@app.get("/")
def read_root():
    return {"status": "Predictor API is running"}

@app.get("/model-info/")
def get_model_info():
    if not model_package:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    
    return {
        "model_type": str(type(model_package['model'])),
        "feature_columns": model_package.get('feature_columns', []),
        "target_column": model_package.get('target_col', 'Unknown'),
        "model_metadata": model_package.get('model_metadata', {}),
        "num_features": len(model_package.get('feature_columns', []))
    }

@app.post("/predict/")
async def predict(request: Request):
    """
    Receives a request, manually parses the JSON body, and returns a prediction.
    """
    if not model_package or not DynamicPredictionInput:
        raise HTTPException(status_code=503, detail="Model is not loaded or initialized properly")

    try:
        # Manually read the raw JSON body from the request
        raw_data = await request.json()
        print(f"--- Raw JSON received --- \n{raw_data}\n-------------------------")

        # Now, parse the raw data using the Pydantic model
        data = DynamicPredictionInput(**raw_data)

        model = model_package['model']
        scaler = model_package.get('scaler')
        feature_columns = model_package['feature_columns']
        
        input_data_dict = data.model_dump()
        input_df = pd.DataFrame([input_data_dict], columns=feature_columns)
        
        print("\n--- Initial DataFrame from Request ---")
        print(input_df.to_string())
        print("------------------------------------\n")

        if scaler is not None:
            scaled_data = scaler.transform(input_df)
            scaled_data = np.nan_to_num(scaled_data, nan=0.0, posinf=0.0, neginf=0.0)
            input_for_prediction = pd.DataFrame(scaled_data, columns=input_df.columns)
        else:
            input_for_prediction = input_df

        print("--- Input for Prediction (After Scaling) ---")
        print(input_for_prediction.to_string())
        print("------------------------------------------")
        
        prediction = model.predict(input_for_prediction)
        
        return {
            "prediction": float(prediction[0]),
            "target_column": model_package.get('target_col', 'unknown'),
            "model_type": str(type(model).__name__)
        }

    except Exception as e:
        logging.error("An error occurred during prediction", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)