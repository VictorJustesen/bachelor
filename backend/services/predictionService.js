const axios = require('axios');

const getPrediction = async (req, res) => {
  try {
    // Get the prediction API URL from environment variable or default
    const PREDICTION_API_URL = process.env.PREDICTOR_SERVICE_URL || "http://predictor:8001";
    
    console.log('Received prediction request:', req.body);

    // First, get model info to understand expected features
    const modelInfoResponse = await axios.get(`${PREDICTION_API_URL}/model-info/`);
    const modelInfo = modelInfoResponse.data;
    
    console.log('Model expects features:', modelInfo.feature_columns);

    // Extract features from request body
    const requestData = req.body;
    
    // Build prediction payload with only the features the model expects
    const predictionPayload = {};
    
    // Map common field names (adjust based on your model's feature names)
    const currentYear = new Date().getFullYear();
    const daysSince1992 = Math.floor((Date.now() - new Date('1992-01-01').getTime()) / (1000 * 60 * 60 * 24));

    const fieldMapping = {
      'm2': 'sqn',
      'V_r_': 'rooms',
      'age': (requestData) => currentYear - parseInt(requestData['age'], 10),
      'date_ordinal': daysSince1992,
      // Add more mappings based on your model's feature columns
    };

    // Only include features that the model expects
    modelInfo.feature_columns.forEach(feature => {
      if (fieldMapping[feature] && requestData[fieldMapping[feature]] !== undefined) {
        predictionPayload[feature] = parseFloat(requestData[fieldMapping[feature]]);
      } else if (requestData[feature] !== undefined) {
        predictionPayload[feature] = parseFloat(requestData[feature]);
      } else {
        // If feature is missing, you might want to use a default value
        // or return an error
        console.warn(`Missing feature: ${feature}`);
        predictionPayload[feature] = 0; // Default value - adjust as needed
      }
    });

    console.log('Sending to prediction API:', predictionPayload);

    // Make prediction request
    const predictionResponse = await axios.post(
      `${PREDICTION_API_URL}/predict/`, 
      predictionPayload,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000 // 10 second timeout
      }
    );

    const predictionResult = predictionResponse.data;
    
    console.log('Prediction result:', predictionResult);

    // Format response for frontend
    res.json({
      estimated_price: Math.round(predictionResult.prediction),
      target_column: predictionResult.target_column,
      model_type: predictionResult.model_type,
      confidence_score: 0.85, // You might want to add this to your ML model
      features_used: Object.keys(predictionPayload)
    });

  } catch (error) {
    console.error("Error calling prediction service:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      res.status(503).json({ 
        error: "Prediction service is unavailable. Please try again later." 
      });
    } else if (error.response) {
      // The prediction API returned an error
      console.error("Prediction API error:", error.response.data);
      res.status(error.response.status).json({ 
        error: error.response.data.detail || "Prediction failed" 
      });
    } else {
      res.status(500).json({ 
        error: "Failed to get prediction from the ML service." 
      });
    }
  }
};


module.exports = { 
  getPrediction,
};