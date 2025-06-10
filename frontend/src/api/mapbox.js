const MAPBOX_ACCESS_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
const GEOCODING_API_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/';

async function fetchFromMapbox(endpoint) {
  const url = `${GEOCODING_API_URL}${endpoint}&access_token=${MAPBOX_ACCESS_TOKEN}`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error("Failed to fetch from Mapbox API");
    throw new Error('Failed to fetch from Mapbox API');
  }
  return res.json();
}

export async function forwardGeocode(address) {
  const endpoint = `${encodeURIComponent(address)}.json?limit=1`;
  const data = await fetchFromMapbox(endpoint);
  return data.features;
}

export async function reverseGeocode(lng, lat) {
  const endpoint = `${lng},${lat}.json?limit=1`;
  const data = await fetchFromMapbox(endpoint);
  return data.features;
}