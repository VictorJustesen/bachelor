const express = require('express');
const router = express.Router();
const { loginUser, getUserInfo } = require('../services/userService');
const { getPrediction } = require('../services/predictionService');

// User Service Routes
router.post('/users/login', loginUser);
router.get('/users/:userId', getUserInfo); // Example: /api/users/1

// Prediction Service Route
router.post('/predict', getPrediction);

module.exports = router;