const axios = require('axios');

const getPrediction = async (req, res) => {
  try {
    const PREDICTION_API_URL = process.env.PREDICTOR_SERVICE_URL || "http://predictor-container:8001";
    console.log('🤖 Received prediction request for:', req.body.address);

    const requestData = req.body;
    
    // WHAT WE GET IN
    console.log('\n📥 WHAT WE GET:');
    console.log(`   Total keys: ${Object.keys(requestData).length}`);
    Object.keys(requestData).forEach((key, i) => {
      if (i < 20) { // Show first 20 keys
        console.log(`   ${i+1}. ${key} = ${requestData[key]}`);
      }
    });
    if (Object.keys(requestData).length > 20) {
      console.log(`   ... and ${Object.keys(requestData).length - 20} more keys`);
    }

    // ✅ SEND ALL THE DATA DIRECTLY - No manual mapping!
    console.log('\n🚀 Sending ALL data directly to prediction service');

    const predictionResponse = await axios.post(
      `${PREDICTION_API_URL}/predict/`,
      requestData,  // ✅ Send everything!
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000
      }
    );

    const prediction = predictionResponse.data;
    console.log('✅ Prediction received:', prediction.prediction);
    
    res.json({
      estimated_price: prediction.prediction,
      model_version: prediction.model_type,
      confidence_score: 0.85,
      price_per_sqm: requestData.sqm ? prediction.prediction / requestData.sqm : null,
      features_used: prediction.features_used
    });

  } catch (error) {
    console.error('❌ Error in getPrediction:', error.message);
    res.status(500).json({ error: 'Prediction service unavailable' });
  }
};

module.exports = { getPrediction };