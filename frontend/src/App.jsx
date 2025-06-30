import { useState, useRef } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import Header from './components/Header/Header'
import Start from './components/Start/Start.jsx'
import Free from './components/Free/Free.jsx'
import Map from './components/Map/Map.jsx'
import { DEFAULT_MAP_PARAMS } from './mapDefaults'
import './App.css'

function App() {
  const [mode, setMode] = useState('start')
  const mapInstance = useRef(null)

  // sample house data
  const houseMarkers = [
    { lngLat: [12.570, 55.685], number: 1, highlight: true },
    { lngLat: [12.568, 55.683], number: 2, highlight: false },
    // ...add more houses as needed
  ]

  const base = DEFAULT_MAP_PARAMS
  const params = {
    ...base,
    ...(mode === 'start'
      ? { interactive: false, spin: true }
      : { interactive: true, spin: false, flyToOnMount: true }),
  }

  return (
    <ThemeProvider>
      <div className="app-container">
        <Header />
        <div className="main-content">
          <Map
            params={params}
            markers={mode === 'start' ? houseMarkers : []}
            onMapLoad={map => { mapInstance.current = map }}
          />
          {mode === 'start' && <Start onEnterFree={() => setMode('free')} />}
          {mode === 'free' && <Free map={mapInstance.current} />}
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App