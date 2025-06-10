import React, { useState, useEffect, useRef } from 'react'
import { forwardGeocode, reverseGeocode } from '../../api/mapbox'
import { getBuildingDetails, getPropertyHistory, estimatePrice } from '../../api/backend'
import './Free.css'

function Free({ map }) {
  if (!map) return null

  const [addressInput, setAddressInput] = useState('')
  const [selectedBuildingId, setSelectedBuildingId] = useState(null)
  const [selectedData, setSelectedData] = useState(null)
  const [estimatedPrice, setEstimatedPrice] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetchingInfo, setIsFetchingInfo] = useState(false)
  const prevBuildingId = useRef(null)
  const hoveredId = useRef(null) // Add ref for hover state

  useEffect(() => {
    if (!map) return
    if (prevBuildingId.current !== null) {
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: prevBuildingId.current },
        { select: false }
      )
    }
    if (selectedBuildingId !== null) {
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: selectedBuildingId },
        { select: true }
      )
    }
    prevBuildingId.current = selectedBuildingId
  }, [map, selectedBuildingId])

  const selectFeature = async (feature, coords) => {
    if (feature) {
      setSelectedBuildingId(feature.id)
      setEstimatedPrice(null)
      map.flyTo({ center: coords, zoom: 18, pitch: 60, essential: true })
      
      const geoFeatures = await reverseGeocode(coords[0], coords[1])
      const address = geoFeatures[0]?.place_name || 'Address not found'
      
      setSelectedData({ address, salesHistory: [] })

    } else {
      setSelectedBuildingId(null)
      setSelectedData(null)
      setEstimatedPrice(null)
    }
  }

  useEffect(() => {
    if (!map) return
    
    // Click handler
    const onClick = async e => {
      const coords = [e.lngLat.lng, e.lngLat.lat]
      const feature = map.queryRenderedFeatures(e.point, { layers: ['3d-buildings'] })[0] || null
      selectFeature(feature, coords)
    }

    // Mouse move handler for hover effect
    const onMouseMove = e => {
      const features = map.queryRenderedFeatures(e.point, { layers: ['3d-buildings'] })
      
      if (features.length > 0) {
        // Change cursor to pointer
        map.getCanvas().style.cursor = 'pointer'
        
        const feature = features[0]
        
        // Remove hover from previous feature
        if (hoveredId.current !== null && hoveredId.current !== feature.id) {
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: hoveredId.current },
            { hover: false }
          )
        }
        
        // Add hover to current feature
        if (hoveredId.current !== feature.id) {
          hoveredId.current = feature.id
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: feature.id },
            { hover: true }
          )
        }
      } else {
        // Reset cursor
        map.getCanvas().style.cursor = ''
        
        // Remove hover from previous feature
        if (hoveredId.current !== null) {
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: hoveredId.current },
            { hover: false }
          )
          hoveredId.current = null
        }
      }
    }

    // Mouse leave handler
    const onMouseLeave = () => {
      map.getCanvas().style.cursor = ''
      
      if (hoveredId.current !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: hoveredId.current },
          { hover: false }
        )
        hoveredId.current = null
      }
    }

    map.on('click', onClick)
    map.on('mousemove', '3d-buildings', onMouseMove)
    map.on('mouseleave', '3d-buildings', onMouseLeave)
    
    return () => {
      map.off('click', onClick)
      map.off('mousemove', '3d-buildings', onMouseMove)
      map.off('mouseleave', '3d-buildings', onMouseLeave)
    }
  }, [map])

  async function handleFlyTo() {
    const features = await forwardGeocode(addressInput)
    if (!features.length) {
        alert("Address not found")
        return
    }
    const [lng, lat] = features[0].center

    map.flyTo({ center: [lng, lat], zoom: 18, pitch: 60, essential: true })

    map.once('moveend', () => {
      const centerPoint = map.project([lng, lat])
      const feature = map.queryRenderedFeatures(centerPoint, {
        layers: ['3d-buildings']
      })[0] || null

      if (feature) {
          selectFeature(feature, [lng, lat])
      } else {
          setSelectedBuildingId(null)
          setSelectedData({ address: features[0].place_name, salesHistory: [] })
          setEstimatedPrice(null)
      }
    })
  }

  async function handleFetchInformation() {
    if (!selectedData || !selectedData.address) return;
    
    setIsFetchingInfo(true);
    try {
      // Fetch both building info and property history
      const [buildingInfo, historyData] = await Promise.all([
        getBuildingDetails(selectedBuildingId, selectedData.address),
        getPropertyHistory(selectedData.address, selectedData.zip)
      ]);
      
      setSelectedData({
        ...selectedData,
        sqm: buildingInfo.sqm,
        rooms: buildingInfo.rooms,
        year: buildingInfo.year,
        zip: buildingInfo.zip,
        city: buildingInfo.city,
        buildingType: buildingInfo.buildingType,
        salesHistory: historyData.salesHistory || buildingInfo.salesHistory || [],
        marketTrends: historyData.marketTrends
      });

    } catch (error) {
      console.error('Error fetching information:', error);
      alert('Fejl ved hentning af information');
    } finally {
      setIsFetchingInfo(false);
    }
  }
  
  async function handleEstimatePrice() {
      if (!selectedData) return
      
      setIsLoading(true)
      try {
        const result = await estimatePrice(selectedData)
        setEstimatedPrice(result)
      } catch (error) {
        console.error('Error estimating price:', error)
        alert('Fejl ved prisberegning')
      } finally {
        setIsLoading(false)
      }
  }

  return (
    <div className="free-controls">
      <div className="address-input">
        <input
          type="text"
          placeholder="Søg på en adresse"
          value={addressInput}
          onChange={e => setAddressInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleFlyTo()}
        />
        <button onClick={handleFlyTo}>Søg</button>
      </div>

      {selectedData && (
        <div className="select-overlay">
          <h3>Ejendomsdata</h3>
          <label>
            Adresse:
            <input type="text" value={selectedData.address} readOnly />
          </label>
          <label>
            Kvadratmeter:
            <input
              type="number"
              value={selectedData.sqm || ''}
              onChange={e => setSelectedData({ ...selectedData, sqm: +e.target.value })}
            />
          </label>
          <label>
            Postnummer:
            <input type="text" value={selectedData.zip || ''} readOnly />
          </label>
          <label>
            By:
            <input type="text" value={selectedData.city || ''} readOnly />
          </label>
          <label>
            Antal rum:
            <input
              type="number"
              value={selectedData.rooms || ''}
              onChange={e => setSelectedData({ ...selectedData, rooms: +e.target.value })}
            />
          </label>
          <label>
            Byggeår:
            <input
              type="number"
              value={selectedData.year || ''}
              onChange={e => setSelectedData({ ...selectedData, year: +e.target.value })}
            />
          </label>

          <h4>Salgshistorik</h4>
          <ul>
            {selectedData.salesHistory?.map((sale, i) => (
              <li key={i}>
                {sale.date}: DKK {sale.price.toLocaleString()} {sale.type && `(${sale.type})`}
              </li>
            ))}
          </ul>

          {/* Market trends if available */}
          {selectedData.marketTrends && (
            <div className="market-trends">
              <h4>Markedsdata</h4>
              <p>Gennemsnitspris per m²: DKK {selectedData.marketTrends.averagePricePerSqm?.toLocaleString()}</p>
              <p>Gennemsnitlig salgstid: {selectedData.marketTrends.averageSellTime} dage</p>
              <p>Prisændring (1 år): {selectedData.marketTrends.priceChange1Year}</p>
            </div>
          )}

          {/* Button for fetching all information */}
          <button onClick={handleFetchInformation} disabled={isFetchingInfo}>
            {isFetchingInfo ? 'Henter information...' : 'Hent information'}
          </button>

          <button onClick={handleEstimatePrice} disabled={isLoading}>
            {isLoading ? 'Beregner...' : 'Beregn pris'}
          </button>

          {/* Display estimated price */}
          {estimatedPrice && (
            <div className="estimated-price">
              <h4>Estimeret pris:</h4>
              <p className="price-value">DKK {estimatedPrice.estimated_price?.toLocaleString()}</p>
              {estimatedPrice.confidence_score && (
                <p className="confidence">Tillid: {(estimatedPrice.confidence_score * 100).toFixed(1)}%</p>
              )}
              {estimatedPrice.model_version && (
                <p className="model-info">Model: {estimatedPrice.model_version}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Free