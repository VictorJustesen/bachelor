const API_BASE_URL = '/api';

async function fetchFromBackend(endpoint, options) {
     console.log(`Fetching from backend: ${API_BASE_URL}/${endpoint}`, options);
     const res = await fetch(`${API_BASE_URL}/${endpoint}`, options);
     if (!res.ok) {
         throw new Error(`Failed to fetch from backend: ${endpoint}`);
     }
     return res.json();
}

export async function getBuildingDetails(address, overrides = {}) {
    try {
        const data = await fetchFromBackend('scrape/building-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, ...overrides })
        });
        console.log(`Building Info: ${JSON.stringify(data)}`);
        return data;
    } catch (error) {
        console.error('Error fetching building details:', error);
        return {
            address: address,
            sqm: 120, 
            zip: '2100', 
            city: 'København',
            rooms: 4, 
            year: 1999, 
            buildingType: 'Apartment',
            salesHistory: [
              { date: '2022-03-10', price: 7500000 },
              { date: '2018-07-22', price: 6200000 },
            ]
        };
    }
}

export async function getPropertyHistory(address, zip) {
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

export const estimatePrice = async (propertyData) => {
    console.log('🚀 Estimating price for property:', propertyData.address);
    
    return fetchFromBackend('predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(propertyData)
    });
};