const express = require('express');
const router = express.Router();
const userRoutes = require('./users');
const { getPrediction } = require('../services/predictionService');
const { getBuildingInfo, getPropertyHistory } = require('../services/scrapeService');
const { optionalAuth } = require('../middleware/auth');

// User Service Routes
router.use('/users', userRoutes);

// Prediction Service Route (with optional authentication to track user predictions)
router.post('/predict', optionalAuth, getPrediction);

// Scrape Service Routes
router.post('/scrape/building-info', getBuildingInfo);
router.post('/scrape/property-history', getPropertyHistory);

module.exports = router;