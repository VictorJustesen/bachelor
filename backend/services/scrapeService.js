const axios = require('axios');

const SCRAPER_SERVICE_URL = process.env.SCRAPER_SERVICE_URL || 'http://localhost:9000';

const getBuildingInfo = async (req, res) => {
  const { address, buildingId } = req.body;

  try {
    console.log(`Requesting building info from scraper service for: ${address}`);
    
    // Call your scraping2 service instead of mock data
    const response = await axios.post(`${SCRAPER_SERVICE_URL}/scrape/building-info`, {
      address: address,
      buildingId: buildingId
    }, {
      timeout: 30000 // 30 second timeout
    });

    res.json(response.data);

  } catch (error) {
    console.error("Error calling scraper service:", error.message);
    
    // Fallback to mock data if scraper service fails
    const mockData = {
      address: address,
      sqm: Math.floor(Math.random() * 200) + 50,
      rooms: Math.floor(Math.random() * 6) + 2,
      year: Math.floor(Math.random() * 50) + 1970,
      zip: Math.floor(Math.random() * 9000) + 1000,
      city: "København",
      buildingType: "Villa",
      salesHistory: [
        {
          date: "2020-03-15",
          price: Math.floor(Math.random() * 2000000) + 1000000
        }
      ],
      source: 'fallback_mock'
    };
    
    res.json(mockData);
  }
};

const getPropertyHistory = async (req, res) => {
  const { address, zip } = req.body;

  try {
    console.log(`Requesting property history from scraper service for: ${address}`);
    
    // You can add a property history endpoint to your scraping2 service
    const response = await axios.post(`${SCRAPER_SERVICE_URL}/scrape/not made yet`, {
      address: address,
      zip: zip
    }, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error) {
    console.error("Error calling scraper service for property history:", error.message);
    
    // Fallback mock data
    const mockHistory = {
      address: address,
      zip: zip,
      salesHistory: [
        {
          date: "2023-06-10",
          price: Math.floor(Math.random() * 3000000) + 1500000,
          sqm: Math.floor(Math.random() * 150) + 75
        }
      ],
      source: 'fallback_mock'
    };
    
    res.json(mockHistory);
  }
};

module.exports = { getBuildingInfo, getPropertyHistory };