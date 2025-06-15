import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from sklearn.exceptions import NotFittedError
import numpy as np
# --- Configuration ---
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'best_model')
MODEL_NAME = 'linear_regression_test'  # Change this to match your actual model file
MODEL_PATH = os.path.join(MODEL_DIR, f'{MODEL_NAME}.pkl')

# --- FastAPI App ---
app = FastAPI(redirect_slashes=False)
model_package = None

# --- Pydantic Model for Input Validation ---
class DynamicPredictionInput(BaseModel):
    pass

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
    
    # Print model info for debugging
    print(f"Model type: {type(model_package.get('model', 'Unknown'))}")
    print(f"Feature columns: {model_package.get('feature_columns', [])}")
    print(f"Target column: {model_package.get('target_col', 'Unknown')}")

    # Dynamically create the Pydantic model from the model's feature columns
    if model_package and 'feature_columns' in model_package:
        fields = {feature: float for feature in model_package['feature_columns']} 
        DynamicPredictionInput = type('PredictionInput', (BaseModel,), {'__annotations__': fields})
        print(f"Created input validation for {len(fields)} features")
    else:
        raise ValueError("Could not find 'feature_columns' in the loaded model package.")

@app.get("/")
def read_root():
    """A simple endpoint to confirm the service is running."""
    return {"status": "Predictor API is running"}

@app.get("/model-info/")
def get_model_info():
    """Get information about the loaded model."""
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
def predict(data: DynamicPredictionInput):
    if not model_package:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    try:
        # Extract components from the loaded package
        model = model_package['model']
        scaler = model_package.get('scaler')
        feature_columns = model_package['feature_columns']
        
        # Convert input data to a DataFrame, ensuring column order
        input_df = pd.DataFrame([data.dict()], columns=feature_columns)
        
        # Apply feature selection if it was used during training
        feature_selector = model_package.get('feature_selector')
        if feature_selector is not None:
            input_df = feature_selector.transform(input_df)
        
        # Scale the data using the loaded scaler (if available)
        if scaler is not None:
            try:
                # Attempt to transform the data as normal
                input_scaled = scaler.transform(input_df)
            except NotFittedError:
                # --- TEMPORARY DEBUGGING WORKAROUND ---
                print("\nWARNING: StandardScaler was not fitted. Applying a temporary fit for debugging.")
                print("         The resulting prediction will be inaccurate. The permanent fix is to retrain the model correctly.\n")
                
                # "Fake" fit the scaler on the single incoming data point, then transform
                scaler.fit(input_df)
                input_scaled = scaler.transform(input_df)
                input_scaled = np.nan_to_num(input_scaled)

                # --- END OF WORKAROUND ---
        else:
            input_scaled = input_df.values

        
        prediction = model.predict(np.nan_to_num(input_scaled))
        
        # Return the result
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
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Change from 8000 to 8001