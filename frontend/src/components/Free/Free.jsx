import React, { useState } from 'react'
import './Free.css'

function Free({ map }) {
  if (!map) return null

  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')

  function handleFlyTo() {
    const latNum = parseFloat(lat)
    const lngNum = parseFloat(lng)
    if (!isNaN(latNum) && !isNaN(lngNum)) {
      map.flyTo({ center: [lngNum, latNum], essential: true })
    }
  }

  return (
    <div className="free-controls">
      <button onClick={() => map.zoomIn()}>Zoom In</button>
      <button onClick={() => map.zoomOut()}>Zoom Out</button>
      <button onClick={() => map.rotateTo(map.getBearing() + 30, { duration: 500 })}>
        Rotate +
      </button>
      <button onClick={() => map.rotateTo(map.getBearing() - 30, { duration: 500 })}>
        Rotate –
      </button>
      <div className="free-flyto">
        <input
          type="text"
          placeholder="lat"
          value={lat}
          onChange={e => setLat(e.target.value)}
        />
        <input
          type="text"
          placeholder="lng"
          value={lng}
          onChange={e => setLng(e.target.value)}
        />
        <button onClick={handleFlyTo}>Go</button>
      </div>
    </div>
  )
}

export default Free
