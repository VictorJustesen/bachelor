const axios = require('axios');

const SCRAPER_SERVICE_URL = process.env.SCRAPER_SERVICE_URL || 'http://localhost:9000';

const getBuildingInfo = async (req, res) => {
  try {
    console.log(`Requesting building info from scraper service for: ${req.body.address}`);
    
    const response = await axios.post(`${SCRAPER_SERVICE_URL}/scrape/building-info`, 
      req.body,
      {
        timeout: 30000 
      }
    );
    
    console.log(response.data);
    res.json(response.data);

  } catch (error) {
    console.error("Error calling scraper service:", error.message);
    
    const mockData = {
      address: req.body.address,
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
    
    const response = await axios.post(`${SCRAPER_SERVICE_URL}/scrape/property-history`, {
      address: address,
      zip: zip
    }, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error) {
    console.error("Error calling scraper service for property history:", error.message);
    
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