import { useState, useRef, useCallback } from 'react';
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

  const handleMapClick = useCallback(async (lngLat) => {
    setPin(lngLat);
    const features = await reverseGeocode(lngLat.lng, lngLat.lat);
    const result = features[0] || {};
    result.center = [lngLat.lng, lngLat.lat];
    if (!result.place_name) {
        result.place_name = `Valgt punkt: ${lngLat.lat.toFixed(4)}, ${lngLat.lng.toFixed(4)}`;
    }

    if (freeComponentRef.current) {
      freeComponentRef.current.handleLocationSelect(result);
    }
  }, []);

  const handleHeaderSearchSelect = (result) => {
    const [lng, lat] = result.center;
    setPin({ lng, lat });
    if (freeComponentRef.current) {
        freeComponentRef.current.handleLocationSelect(result);
    }
  };
  
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
            onMapLoad={onMapLoad}
            onMapClick={handleMapClick}
          />
          {mode === 'start' && <Start onEnterFree={() => setMode('free')} />}
          {mode === 'free' && <Free ref={freeComponentRef} map={mapInstance.current} />}
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;