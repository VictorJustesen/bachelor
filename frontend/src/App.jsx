import { useState, useRef } from 'react';
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

  const handleMapClick = async (lngLat) => {
    setPin(lngLat);
    const features = await reverseGeocode(lngLat.lng, lngLat.lat);
    const address = features[0]?.place_name || 'Address not found';

    if (freeComponentRef.current) {
      freeComponentRef.current.handleLocationSelect({
        address: address,
        center: [lngLat.lng, lngLat.lat]
      });
    }
  };

  const handleHeaderSearchSelect = (result) => {
    setPin({ lng: result.center[0], lat: result.center[1] });
    if (freeComponentRef.current) {
        freeComponentRef.current.handleLocationSelect(result);
    }
  };

  return (
    <ThemeProvider>
      <div className="app-container">
        <Header mode={mode} onSearchSelect={handleHeaderSearchSelect} />
        <div className="main-content">
          <Map
            params={params}
            pin={pin}
            onMapLoad={map => { mapInstance.current = map; }}
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