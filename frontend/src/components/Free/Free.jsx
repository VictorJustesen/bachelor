import React, { useState, useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import './Free.css'

function Free({ map }) {
  if (!map) return null

  const [addressInput, setAddressInput] = useState('')
  const [selectedBuildingId, setSelectedBuildingId] = useState(null)
  const [selectedData, setSelectedData] = useState(null)
  const prevBuildingId = useRef(null)

  // whenever selectedBuildingId changes, clear old hover and set new hover
  useEffect(() => {
    if (!map) return
    // clear old
    if (prevBuildingId.current != null) {
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: prevBuildingId.current },
        { select: false }
      )
    }
    // set new
    if (selectedBuildingId != null) {
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: selectedBuildingId },
        { select: true }
      )
      map.getCanvas().style.cursor = 'pointer'
    } else {
      map.getCanvas().style.cursor = ''
    }
    prevBuildingId.current = selectedBuildingId

    return () => {
      if (prevBuildingId.current != null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: prevBuildingId.current },
          { select: false }
        )
      }
    }
  }, [map, selectedBuildingId])

  // unify select logic so it always shows data and only highlights if feature exists
  const selectFeature = (feature, coords, data) => {
    setSelectedData(data) // always show overlay

    if (feature) {
      setSelectedBuildingId(feature.id)
    } else {
      setSelectedBuildingId(null)
    }
    map.flyTo({ center: coords, essential: true })
  }

  // 1) click‐handler: reverse‐geocode on e.lngLat
  useEffect(() => {
    if (!map) return
    const onClickBuilding = async e => {
      const [lng, lat] = [e.lngLat.lng, e.lngLat.lat]
      // reverse‐geocode via coords
      const rev = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/` +
        `${lng},${lat}.json?access_token=${mapboxgl.accessToken}&limit=1`
      )
      const revJson = await rev.json()
      const address = revJson.features[0]?.place_name || 'Unknown address'

      const feat = map.queryRenderedFeatures(e.point, { layers: ['3d-buildings'] })[0] || null
      selectFeature(feat, [lng, lat], {
        address,
        sqm: 100, zip: '12345', city: 'SampleCity',
        rooms: 3, year: 2005, houseType: 'Detached',
        region: 'Downtown',
        salesHistory: [
          { date: '2021-01-01', price: 600000 },
          { date: '2019-06-15', price: 550000 }
        ]
      })
    }
    map.on('click', onClickBuilding)
    return () => { map.off('click', onClickBuilding) }
  }, [map])

  // 2) handleFlyTo: forward‐geocode to coords, then reverse‐geocode to get place_name
  async function handleFlyTo() {
    // 1) forward‐geocode to get [lng,lat]
    const fwd = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/` +
      `${encodeURIComponent(addressInput)}.json?access_token=${mapboxgl.accessToken}&limit=1`
    )
    const { features: f } = await fwd.json()
    if (!f.length) return
    const [lng, lat] = f[0].center

    // 2) reverse‐geocode to get the clean address
    const rev = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/` +
      `${lng},${lat}.json?access_token=${mapboxgl.accessToken}&limit=1`
    )
    const revJson = await rev.json()
    const address = revJson.features[0]?.place_name || f[0].place_name

    // 3) fly there
    map.flyTo({ center: [lng, lat], essential: true })

    // 4) once flight is done, pick the building under the center
    map.once('moveend', () => {
      const centerPoint = map.project([lng, lat])
      const feat = map.queryRenderedFeatures(centerPoint, {
        layers: ['3d-buildings']
      })[0] || null

      selectFeature(feat, [lng, lat], {
        address,
        sqm: 100,
        zip: '12345',
        city: 'SampleCity',
        rooms: 3,
        year: 2005,
        houseType: 'Detached',
        region: 'Downtown',
        salesHistory: [
          { date: '2021-01-01', price: 600000 },
          { date: '2019-06-15', price: 550000 }
        ]
      })
    })
  }

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

      <div className="address-input">
        <input
          type="text"
          placeholder="Adresse"
          value={addressInput}
          onChange={e => setAddressInput(e.target.value)}
        />
        <button onClick={handleFlyTo}>Go</button>
      </div>

      {selectedData && (
        <div className="select-overlay">
          <h3>Building Details</h3>
          <label>Address:
            <input
              value={selectedData.address}
              onChange={e => setSelectedData({ ...selectedData, address: e.target.value })}
            />
          </label>
          <label>SQM:
            <input
              type="number"
              value={selectedData.sqm}
              onChange={e => setSelectedData({ ...selectedData, sqm: +e.target.value })}
            />
          </label>
          {/* …other fields… */}
          <button onClick={() => alert('Estimate Price')}>Estimate Price</button>
        </div>
      )}
    </div>
  )
}

export default Free
