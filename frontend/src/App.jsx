import { useState, useRef, useCallback } from 'react'; // 1. Import useCallback
import { ThemeProvider } from './contexts/ThemeContext';
import Header from './components/Header/Header';
import Start from './components/Start/Start.jsx';
import Free from './components/Free/Free.jsx';
import Map from './components/Map/Map.jsx';
import { DEFAULT_MAP_PARAMS } from './mapDefaults';
import { reverseGeocode } from './api/mapbox.js';
import './App.css';

function App() {
  const [mode, setMode] = useState('start');
  const [pin, setPin] = useState(null);
  const mapInstance = useRef(null);
  const freeComponentRef = useRef(null);

  const base = DEFAULT_MAP_PARAMS;
  const params = {
    ...base,
    ...(mode === 'start'
      ? { interactive: false, spin: true }
      : { interactive: true, spin: false, flyToOnMount: true }),
  };

  // 2. Wrap handleMapClick in useCallback
  const handleMapClick = useCallback(async (lngLat) => {
    setPin(lngLat);
    const features = await reverseGeocode(lngLat.lng, lngLat.lat);
    const address = features[0]?.place_name || 'Address not found';

    if (freeComponentRef.current) {
      freeComponentRef.current.handleLocationSelect({
        address: address,
        center: [lngLat.lng, lngLat.lat]
      });
    }
  }, []); // Dependencies are empty as setPin and reverseGeocode are stable

  const handleHeaderSearchSelect = (result) => {
    setPin({ lng: result.center[0], lat: result.center[1] });
    if (freeComponentRef.current) {
        freeComponentRef.current.handleLocationSelect(result);
    }
  };
  
  // Also wrap onMapLoad for consistency
  const onMapLoad = useCallback(map => {
    mapInstance.current = map;
  }, []);

  return (
    <ThemeProvider>
      <div className="app-container">
        <Header mode={mode} onSearchSelect={handleHeaderSearchSelect} />
        <div className="main-content">
          <Map
            params={params}
            pin={pin}
            onMapLoad={onMapLoad} // Pass the memoized function
            onMapClick={handleMapClick} // Pass the memoized function
          />
          {mode === 'start' && <Start onEnterFree={() => setMode('free')} />}
          {mode === 'free' && <Free ref={freeComponentRef} map={mapInstance.current} />}
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;