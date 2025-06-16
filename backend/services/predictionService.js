const axios = require('axios');

const getPrediction = async (req, res) => {
  try {
    const PREDICTION_API_URL = process.env.PREDICTOR_SERVICE_URL || "http://predictor:8001";
    console.log('Received prediction request:', req.body);

    const modelInfoResponse = await axios.get(`${PREDICTION_API_URL}/model-info/`);
    const modelInfo = modelInfoResponse.data;

    const requestData = req.body;
    const predictionPayload = {};

    // --- 1. Initialize all expected features to a default of 0 ---
    modelInfo.feature_columns.forEach(feature => {
      predictionPayload[feature] = 0;
    });

    // --- 2. Map direct and simple calculated values ---
    const currentYear = new Date().getFullYear(); // e.g., 2025
    predictionPayload['V_r_'] = parseFloat(requestData['rooms']);
    predictionPayload['m2'] = parseFloat(requestData['sqm']);
    predictionPayload['age'] = currentYear - parseInt(requestData['year'], 10); // 2025 - 1980 = 45
    predictionPayload['date_ordinal'] = Math.floor((Date.now() - new Date('1992-01-01').getTime()) / (1000 * 60 * 60 * 24));

    // --- 3. Handle one-hot encoded 'building type' features ---
    // Example: if buildingType is "Villa", this sets `btype_Villa` to 1.
    const buildingType = requestData.buildingType;
    const btypeFeature = `btype_${buildingType.replace(/\s/g, '_')}`;
    if (predictionPayload.hasOwnProperty(btypeFeature)) {
      predictionPayload[btypeFeature] = 1;
    }

    // --- 4. Handle one-hot encoded 'region' features (NEEDS YOUR LOGIC) ---
    // You must implement a way to map zip code/city to a region name.
    // This is just a placeholder:
    const regionName = 'Nordsj_lland'; // <-- Replace with your logic to get this from zip '2960'
    const regionFeature = `omr_de_${regionName}`;
    if (predictionPayload.hasOwnProperty(regionFeature)) {
        predictionPayload[regionFeature] = 1;
    }

    // --- 5. Handle complex/lookup features (NEEDS YOUR LOGIC) ---
    // These require looking up historical data, which is a larger task.
    // For now, they will remain 0, but this is where you would calculate them.
    // predictionPayload['pris_pr_m2_mean_365D_postnummer'] = await getAvgPriceForZip(requestData.zip);
    // predictionPayload['mean_of_5_neighbors_pris'] = await getNeighborPrices(requestData.address);

    console.log('Sending to prediction API:', predictionPayload);

    const predictionResponse = await axios.post(
      `${PREDICTION_API_URL}/predict/`,
      predictionPayload,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000
      }
    );

    res.json({
        estimated_price: Math.round(predictionResponse.data.prediction),
        ...predictionResponse.data
    });

  } catch (error) {
    // ... error handling ...
    console.error("Error calling prediction service:", error.message);
    if (error.code === 'ECONNREFUSED') {
      res.status(503).json({
        error: "Prediction service is unavailable. Please try again later."
      });
    } else if (error.response) {
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