const API_BASE_URL = '/api'; // Your backend URL

async function fetchFromBackend(endpoint, options) {
     console.log(`Fetching from backend: ${API_BASE_URL}/${endpoint}`, options);
     const res = await fetch(`${API_BASE_URL}/${endpoint}`, options);
     if (!res.ok) {
         throw new Error(`Failed to fetch from backend: ${endpoint}`);
     }
     return res.json();
}

export async function getBuildingDetails(buildingId, address) {
    // Now uses the scrape service
    try {
        const data = await fetchFromBackend('scrape/building-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ buildingId, address })
        });
        return data;
    } catch (error) {
        console.error('Error fetching building details:', error);
        // Fallback to mock data if API fails
        return {
            address: address,
            sqm: 120, 
            zip: '2100', 
            city: 'København',
            rooms: 4, 
            year: 1999, 
            houseType: 'Apartment',
            region: 'Østerbro',
            salesHistory: [
              { date: '2022-03-10', price: 7500000 },
              { date: '2018-07-22', price: 6200000 },
            ]
        };
    }
}

export async function getPropertyHistory(address, zip) {
    // New function for property history
    try {
        const data = await fetchFromBackend('scrape/property-history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, zip })
        });
        return data;
    } catch (error) {
        console.error('Error fetching property history:', error);
        throw error;
    }
}

export async function estimatePrice(buildingDetails) {
    try {
        console.log('Calling backend for price estimation:', buildingDetails);
        
        // Change from 'predictor/predict' to 'predict' to go through backend
        const estimate = await fetchFromBackend('predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildingDetails)
        });
        
        console.log('Backend response:', estimate);
        return estimate;
        
    } catch (error) {
        console.error('Error estimating price:', error);
        throw error;
    }
}