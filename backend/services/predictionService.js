const axios = require('axios');

const getPrediction = async (req, res) => {
  // This is the data sent from the React frontend
  const { sqm, zip_code, year_built, house_type } = req.body;

  // URL of your separate prediction API (where your ML model is served)
  const PREDICTION_API_URL = "http://localhost:8001/make_prediction"; // Example URL

  const modelFeatures = {
    sqm,
    zip_code,
    year_built,
    house_type,
    // ... you would add all other required features for your model here
  };

  try {
    // In a real scenario, you'd make a call to your ML service
    // const response = await axios.post(PREDICTION_API_URL, modelFeatures);
    // const predictionResult = response.data;

    // --- For now, we'll just return a fake result ---
    console.log(`Simulating call to prediction API with data:`, modelFeatures);
    const estimated_price = (sqm * 20000) + (2024 - year_built) * -1000;
    const predictionResult = {
      estimated_price: Math.round(estimated_price / 1000) * 1000,
      confidence_score: 0.85,
      model_version: "xgboost-v1.2.3"
    };
    // --- End of fake result ---

    res.json(predictionResult);

  } catch (error) {
    console.error("Error calling prediction service:", error.message);
    res.status(500).json({ error: "Failed to get prediction from the ML service." });
  }
};

module.exports = { getPrediction };