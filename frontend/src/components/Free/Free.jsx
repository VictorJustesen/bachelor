import React, { useEffect, useState, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder'
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css'
import './Free.css'

function Free({ map }) {
  const [selectedData, setSelectedData] = useState(null)
  const selectedIdRef = useRef(null)

  useEffect(() => {
    if (!map) return

    const geocoder = new MapboxGeocoder({
      accessToken: mapboxgl.accessToken,
      mapboxgl,
      placeholder: 'Search for address…',
      marker: false
    })

    geocoder.addTo('#geocoder-container')

    // helper to clear previous highlight and set new one
    function highlightBuilding(featureId) {
      if (selectedIdRef.current !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: selectedIdRef.current },
          { hover: false }
        )
      }
      selectedIdRef.current = featureId
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: featureId },
        { hover: true }
      )
      map.getCanvas().style.cursor = 'pointer'
    }

    // geocoder → flyTo + highlight
    geocoder.on('result', ev => {
      const [lng, lat] = ev.result.center
      map.flyTo({ center: [lng, lat], essential: true })

      geocoder.clear()
      const input = document.querySelector('.mapboxgl-ctrl-geocoder input')
      if (input) input.blur()

      const pt = map.project([lng, lat])
      const features = map.queryRenderedFeatures(pt, { layers: ['3d-buildings'] })
      if (features.length) highlightBuilding(features[0].id)
    })

    // direct clicks on buildings should do the same
    function onMapClick(e) {
      const features = map.queryRenderedFeatures(e.point, { layers: ['3d-buildings'] })
      if (features.length) {
        const fid = features[0].id
        highlightBuilding(fid)

        // ← set up your select-overlay data here
        setSelectedData({
          address: '123 Example St',
          sqm: 85,
          zip: '90210',
          city: 'Sample City',
          rooms: 2,
          year: 1995,
          houseType: 'Townhouse',
          region: 'Downtown',
          salesHistory: [
            { date: '2022-01-01', price: 750000 },
            { date: '2020-06-15', price: 700000 }
          ]
        })
      } else {
        // click off builds closes select‐mode
        setSelectedData(null)
      }
    }
    map.on('click', onMapClick)

    return () => {
      geocoder.clear()
      map.removeControl(geocoder)
      map.off('click', onMapClick)
      // clear last highlight
      if (selectedIdRef.current !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: selectedIdRef.current },
          { hover: false }
        )
      }
    }
  }, [map])

  if (!map) return null

  return (
    <div className="free-controls">
      <button onClick={() => map.zoomIn()}>Zoom In</button>
      <button onClick={() => map.zoomOut()}>Zoom Out</button>
      <button onClick={() => map.rotateTo(map.getBearing() + 30, { duration: 500 })}>
        Rotate left
      </button>
      <button onClick={() => map.rotateTo(map.getBearing() - 30, { duration: 500 })}>
        Rotate right
      </button>

      {/* geocoder UI */}
      <div id="geocoder-container" className="address-input" />

      {/* Select overlay */}
      {selectedData && (
        <div className="select-overlay">
          <h3>Building Details</h3>
          <label>
            Address:
            <input
              value={selectedData.address}
              onChange={e => setSelectedData({ ...selectedData, address: e.target.value })}
            />
          </label>
          <label>
            SQM:
            <input
              type="number"
              value={selectedData.sqm}
              onChange={e => setSelectedData({ ...selectedData, sqm: +e.target.value })}
            />
          </label>
          <label>
            Zip Code:
            <input
              value={selectedData.zip}
              onChange={e => setSelectedData({ ...selectedData, zip: e.target.value })}
            />
          </label>
          <label>
            City:
            <input
              value={selectedData.city}
              onChange={e => setSelectedData({ ...selectedData, city: e.target.value })}
            />
          </label>
          <label>
            Rooms:
            <input
              type="number"
              value={selectedData.rooms}
              onChange={e => setSelectedData({ ...selectedData, rooms: +e.target.value })}
            />
          </label>
          <label>
            Year Built:
            <input
              type="number"
              value={selectedData.year}
              onChange={e => setSelectedData({ ...selectedData, year: +e.target.value })}
            />
          </label>
          <label>
            House Type:
            <input
              value={selectedData.houseType}
              onChange={e => setSelectedData({ ...selectedData, houseType: e.target.value })}
            />
          </label>
          <label>
            Region:
            <input
              value={selectedData.region}
              onChange={e => setSelectedData({ ...selectedData, region: e.target.value })}
            />
          </label>

          <h4>Sales History</h4>
          <ul>
            {selectedData.salesHistory.map((sale, i) => (
              <li key={i}>
                {sale.date}: ${sale.price.toLocaleString()}
              </li>
            ))}
          </ul>

          <button onClick={() => alert('Estimating price...')}>
            Estimate Price
          </button>
        </div>
      )}
    </div>
  )
}

export default Free
