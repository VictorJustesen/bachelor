const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 9000;

app.use(cors());
app.use(express.json());

const SERVICE_USERNAME = "XEVPPQIYSU";
const SERVICE_PASSWORD = "Luffygear3!";

// Force console output to be unbuffered
process.stdout.write(''); // Force flush
console.log = (...args) => {
  process.stdout.write(args.join(' ') + '\n');
};
console.error = (...args) => {
  process.stderr.write(args.join(' ') + '\n');
};

app.post('/scrape/building-info', async (req, res) => {
  const { address } = req.body;
  console.log(`Scraping building info for: ${address}`);
  try {
    const pythonResult = await callPropertyScraper(address);

    if (pythonResult.success && pythonResult.data) {
      const data = pythonResult.data;
      
      res.json({
        address: data.address,
        sqm: extractSqmFromData(data.apartment_data),
        rooms: extractRoomsFromData(data.apartment_data),
        year: extractYearFromData(data.building_data),
        zip: extractZipFromAddress(data.address),
        city: extractCityFromAddress(data.address),
        buildingType: extractBuildingType(data.building_data),
        coordinates: data.coordinates,
        salesHistory: data.sales_history,
        source: 'danish_property_scraper',
        apartment_id: data.apartment_id,
        adgangsadresse_id: data.adgangsadresse_id,
        bfe_number: data.bfe_number
      });
    } else {
      console.warn('Python scraper returned no data, using mock data');
      res.json(generateMockBuildingData(address));
    }

  } catch (error) {
    console.error('Property scraping failed:', error);
    res.json(generateMockBuildingData(address));
  }
});

// Add the missing property history endpoint
app.post('/scrape/property-history', async (req, res) => {
  const { address, zip } = req.body;
  
  try {
    console.log(`Scraping property history for: ${address}, ${zip}`);
    
    // Use your Python scraper to get sales history
    const pythonResult = await callPropertyScraper(address);
    
    if (pythonResult.success && pythonResult.data) {
      const data = pythonResult.data;
      
      res.json({
        address: data.address,
        zip: extractZipFromAddress(data.address),
        salesHistory: data.sales_history || [],
        source: 'danish_property_scraper'
      });
    } else {
      res.json({
        address: address,
        zip: zip,
        salesHistory: [
          {
            date: "2023-01-15",
            price: Math.floor(Math.random() * 2000000) + 1000000
          }
        ],
        source: 'mock_fallback'
      });
    }

  } catch (error) {
    console.error('Property history scraping failed:', error);
    res.status(500).json({ error: 'Failed to get property history' });
  }
});

async function callPropertyScraper(address) {
  return new Promise((resolve) => {
    const python = spawn('python3', ['-c', `
import sys
sys.path.append('${__dirname}')
from property_scraper import scrape_property_data
import json

result = scrape_property_data('${address}', '${SERVICE_USERNAME}', '${SERVICE_PASSWORD}')
print(json.dumps(result))
`]);
    
    let stdout = '';
    let stderr = '';
    
    python.stdout.on('data', (data) => {
      console.log(`Python stdout: ${data}`);
      stdout += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      console.error(`Python stderr: ${data}`);
      stderr += data.toString();
    });
    
    python.on('close', (code) => {
      if (code === 0 && stdout.trim()) {
        try {
          const result = JSON.parse(stdout.trim());
          resolve({ success: true, data: result });
        } catch (e) {
          resolve({ success: false, error: 'JSON parse error' });
        }
      } else {
        resolve({ success: false, error: stderr || 'Python script failed' });
      }
    });

    setTimeout(() => {
      python.kill();
      resolve({ success: false, error: 'Timeout' });
    }, 30000);
  });
  
}

function extractSqmFromData(apartmentData) {
  if (!apartmentData || !Array.isArray(apartmentData)) return null;
  
  for (const apartment of apartmentData) {
    // Use the correct field names from the actual data
    if (apartment.enh027ArealTilBeboelse) {
      return parseFloat(apartment.enh027ArealTilBeboelse);
    }
    // Fallback to total area if specific living area not available
    if (apartment.enh026EnhedensSamledeAreal) {
      return parseFloat(apartment.enh026EnhedensSamledeAreal);
    }
  }
  return null;
}

function extractRoomsFromData(apartmentData) {
  if (!apartmentData || !Array.isArray(apartmentData)) return null;
  
  for (const apartment of apartmentData) {
    // Use the correct field name with Danish characters
    if (apartment.enh031AntalVærelser) {
      return parseInt(apartment.enh031AntalVærelser);
    }
  }
  return null;
}

function extractYearFromData(buildingData) {
  if (!buildingData || !Array.isArray(buildingData)) return null;
  
  for (const building of buildingData) {
    // Use the correct field name
    if (building.byg026Opførelsesår) {
      return parseInt(building.byg026Opførelsesår);
    }
  }
  return null;
}

function extractZipFromAddress(address) {
  if (!address) return null;
  const zipMatch = address.match(/\b\d{4}\b/);
  return zipMatch ? zipMatch[0] : null;
}

function extractCityFromAddress(address) {
  if (!address) return null;
  const parts = address.split(' ');
  return parts[parts.length - 1] || null;
}

function extractBuildingType(buildingData) {
  if (!buildingData || !Array.isArray(buildingData)) return 'Unknown';
  
  for (const building of buildingData) {
    if (building.byg021BygningensAnvendelse) {
      // Convert code to readable text
      const code = building.byg021BygningensAnvendelse;
      if (code === "120") return "Residential Building";
      if (code === "920") return "Auxiliary Building";
      return `Building Type ${code}`;
    }
  }
  return 'Residential Building';
}

function generateMockBuildingData(address) {
  return {
    address: address,
    sqm: Math.floor(Math.random() * 200) + 50,
    rooms: Math.floor(Math.random() * 6) + 2,
    year: Math.floor(Math.random() * 50) + 1970,
    zip: '1000',
    city: 'København',
    buildingType: 'Boligbyggeri',
    coordinates: [55.6761, 12.5683],
    salesHistory: [],
    source: 'mock_data'
  };
}

app.listen(PORT, () => {
  console.log(`tScraping server running on port ${PORT} t`);
});