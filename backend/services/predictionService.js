const axios = require('axios');
const { sequelize } = require('../config/database');
const userService = require('./userService');


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
    const buildingType = requestData.buildingType;
    const btypeFeature = `btype_${buildingType.replace(/\s/g, '_')}`;
    if (predictionPayload.hasOwnProperty(btypeFeature)) {
      predictionPayload[btypeFeature] = 1;
    }

    // --- 4. Handle one-hot encoded 'region' features ---
    const regionName = 'Nordsj_lland'; // <-- Replace with your logic to get this from zip '2960'
    const regionFeature = `omr_de_${regionName}`;
    if (predictionPayload.hasOwnProperty(regionFeature)) {
        predictionPayload[regionFeature] = 1;
    }

    console.log('Sending to prediction API:', predictionPayload);

    const predictionResponse = await axios.post(
      `${PREDICTION_API_URL}/predict/`,
      predictionPayload,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000
      }
    );

    const prediction = predictionResponse.data;
    res.json(prediction);

  } catch (error) {
    console.error('Error in getPrediction:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};


module.exports = { 
  getPrediction,
};