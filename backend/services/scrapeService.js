const axios = require('axios');

const getBuildingInfo = async (req, res) => {
  const { address, buildingId } = req.body;

  try {
    // Mock building information - in real scenario you'd call an external API or scraping service
    console.log(`Scraping building info for address: ${address}, buildingId: ${buildingId}`);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const buildingInfo = {
      address: address,
      sqm: Math.floor(Math.random() * 200) + 50, // Random between 50-250
      rooms: Math.floor(Math.random() * 6) + 2, // Random between 2-8
      year: Math.floor(Math.random() * 50) + 1970, // Random between 1970-2020
      zip: Math.floor(Math.random() * 9000) + 1000, // Random zip code
      city: "København", // Default city
      buildingType: "Villa",
      salesHistory: [
        {
          date: "2020-03-15",
          price: Math.floor(Math.random() * 2000000) + 1000000
        },
        {
          date: "2015-08-22", 
          price: Math.floor(Math.random() * 1500000) + 800000
        }
      ]
    };

    res.json(buildingInfo);

  } catch (error) {
    console.error("Error scraping building info:", error.message);
    res.status(500).json({ error: "Failed to scrape building information." });
  }
};

const getPropertyHistory = async (req, res) => {
  const { address, zip } = req.body;

  try {
    console.log(`Scraping property history for address: ${address}, zip: ${zip}`);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const propertyHistory = {
      address: address,
      zip: zip,
      salesHistory: [
        {
          date: "2023-06-10",
          price: Math.floor(Math.random() * 3000000) + 2000000,
          type: "Alm. Salg"
        },
        {
          date: "2019-11-22", 
          price: Math.floor(Math.random() * 2500000) + 1500000,
          type: "Alm. Salg"
        },
        {
          date: "2015-03-05",
          price: Math.floor(Math.random() * 2000000) + 1000000,
          type: "Alm. Salg"
        }
      ],
      marketTrends: {
        averagePricePerSqm: Math.floor(Math.random() * 20000) + 30000,
        averageSellTime: Math.floor(Math.random() * 90) + 30, // days
        priceChange1Year: (Math.random() * 20 - 10).toFixed(1) + '%' // -10% to +10%
      }
    };

    res.json(propertyHistory);

  } catch (error) {
    console.error("Error scraping property history:", error.message);
    res.status(500).json({ error: "Failed to scrape property history." });
  }
};

module.exports = { getBuildingInfo, getPropertyHistory };