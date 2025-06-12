import React, { useState, useEffect, useRef } from 'react'
import { forwardGeocode, reverseGeocode } from '../../api/mapbox'
import { getBuildingDetails, getPropertyHistory, estimatePrice } from '../../api/backend'
import './Free.css'

function Free({ map }) {
  if (!map) return null

  const [addressInput, setAddressInput] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedBuildingId, setSelectedBuildingId] = useState(null)
  const [selectedData, setSelectedData] = useState(null)
  const [estimatedPrice, setEstimatedPrice] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetchingInfo, setIsFetchingInfo] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const prevBuildingId = useRef(null)
  const hoveredId = useRef(null)
  const searchTimeoutRef = useRef(null)
  const dropdownRef = useRef(null)

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

  // Handle search input with debouncing
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (addressInput.length > 2) {
      setIsSearching(true)
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const features = await forwardGeocode(addressInput + ' Denmark')
          
          // Filter to only show addresses with house numbers
          const filteredFeatures = features.filter(feature => {
            const placeType = feature.place_type || []
            const placeName = feature.place_name || ''
            
            // Only include addresses that have house numbers
            return placeType.includes('address') && 
                   /\d+/.test(placeName) && // Contains numbers (house number)
                   !placeType.includes('poi') // Not a point of interest
          })
          
          setSearchResults(filteredFeatures.slice(0, 5))
          setShowDropdown(filteredFeatures.length > 0)
        } catch (error) {
          console.error('Search error:', error)
          setSearchResults([])
          setShowDropdown(false)
        } finally {
          setIsSearching(false)
        }
      }, 300) // 300ms debounce
    } else {
      setSearchResults([])
      setShowDropdown(false)
      setIsSearching(false)
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [addressInput])

  // Handle clicking outside dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectFeature = async (feature, coords) => {
    if (feature) {
      setSelectedBuildingId(feature.id)
      setEstimatedPrice(null)
      map.flyTo({ center: coords, zoom: 18, pitch: 60, essential: true })
      
      const geoFeatures = await reverseGeocode(coords[0], coords[1])
      const address = geoFeatures[0]?.place_name || 'Address not found'
      
      setSelectedData({ address, salesHistory: [] })
      
      // Auto-fetch information after selecting a building
      setTimeout(() => {
        handleFetchInformation({ address, salesHistory: [] }, feature.id)
      }, 1000) // Wait 1 second for map animation to complete

    } else {
      setSelectedBuildingId(null)
      setSelectedData(null)
      setEstimatedPrice(null)
    }
  }

  // Handle search result selection
  const handleSelectResult = async (result) => {
    const [lng, lat] = result.center
    setAddressInput(result.place_name)
    setShowDropdown(false)
    setSearchResults([])

    // Fly to location
    map.flyTo({ center: [lng, lat], zoom: 18, pitch: 60, essential: true })

    // Wait for map to finish moving, then find building
    map.once('moveend', async () => {
      const centerPoint = map.project([lng, lat])
      const feature = map.queryRenderedFeatures(centerPoint, {
        layers: ['3d-buildings']
      })[0] || null

      if (feature) {
        setSelectedBuildingId(feature.id)
        setEstimatedPrice(null)
        
        const selectedDataObj = { 
          address: result.place_name, 
          salesHistory: [] 
        }
        setSelectedData(selectedDataObj)
        
        // Auto-fetch information
        setTimeout(() => {
          handleFetchInformation(selectedDataObj, feature.id)
        }, 500)
      } else {
        setSelectedBuildingId(null)
        setSelectedData({ 
          address: result.place_name, 
          salesHistory: [] 
        })
        setEstimatedPrice(null)
      }
    })
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
        map.getCanvas().style.cursor = 'pointer'
        
        const feature = features[0]
        
        if (hoveredId.current !== null && hoveredId.current !== feature.id) {
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: hoveredId.current },
            { hover: false }
          )
        }
        
        if (hoveredId.current !== feature.id) {
          hoveredId.current = feature.id
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: feature.id },
            { hover: true }
          )
        }
      } else {
        map.getCanvas().style.cursor = ''
        
        if (hoveredId.current !== null) {
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: hoveredId.current },
            { hover: false }
          )
          hoveredId.current = null
        }
      }
    }

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

  async function handleFetchInformation(dataOverride = null, buildingIdOverride = null) {
    const currentData = dataOverride || selectedData
    const currentBuildingId = buildingIdOverride || selectedBuildingId
    
    if (!currentData || !currentData.address) return

    setIsFetchingInfo(true)
    try {
      const [buildingInfo, historyData] = await Promise.all([
        getBuildingDetails(currentBuildingId, currentData.address),
        getPropertyHistory(currentData.address, currentData.zip)
      ])
      
      const updatedData = {
        ...currentData,
        sqm: buildingInfo.sqm,
        rooms: buildingInfo.rooms,
        year: buildingInfo.year,
        zip: buildingInfo.zip,
        city: buildingInfo.city,
        buildingType: buildingInfo.buildingType,
        salesHistory: historyData.salesHistory || buildingInfo.salesHistory || [],
        marketTrends: historyData.marketTrends
      }
      
      setSelectedData(updatedData)

    } catch (error) {
      console.error('Error fetching information:', error)
      alert('Fejl ved hentning af information')
    } finally {
      setIsFetchingInfo(false)
    }
  }
  
  async function handleEstimatePrice() {
    if (!selectedData) return
    
    setIsLoading(true)
    try {
      const estimate = await estimatePrice(selectedData)
      setEstimatedPrice(estimate)
    } catch (error) {
      console.error('Error estimating price:', error)
      alert('Fejl ved prisberegning')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="free-controls">
      {/* Combined search input with dropdown */}
      <div className="address-search" ref={dropdownRef}>
        <div className="search-input-container">
          <input
            type="text"
            placeholder="Søg på en adresse i Danmark..."
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && searchResults.length > 0) {
                handleSelectResult(searchResults[0])
              }
            }}
            className="address-input"
          />
          {isSearching && <div className="search-spinner">🔄</div>}
        </div>
        
        {/* Search results dropdown */}
        {showDropdown && searchResults.length > 0 && (
          <div className="search-dropdown">
            {searchResults.map((result, index) => (
              <div
                key={index}
                className="search-result-item"
                onClick={() => handleSelectResult(result)}
              >
                <div className="result-text">{result.place_name}</div>
                <div className="result-context">{result.context?.find(c => c.id?.includes('country'))?.text}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedData && (
        <div className="select-overlay">
          <h3>Ejendomsdata</h3>
          <label>
            Adresse:
            <input 
              type="text" 
              value={selectedData.address} 
              onChange={e => setSelectedData({ ...selectedData, address: e.target.value })}
            />
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
            <input 
              type="text" 
              value={selectedData.zip || ''} 
              onChange={e => setSelectedData({ ...selectedData, zip: e.target.value })}
            />
          </label>
          <label>
            By:
            <input 
              type="text" 
              value={selectedData.city || ''} 
              onChange={e => setSelectedData({ ...selectedData, city: e.target.value })}
            />
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
                {sale.date}: DKK {sale.price?.toLocaleString()} {sale.type && `(${sale.type})`}
              </li>
            ))}
          </ul>

          {selectedData.marketTrends && (
            <div className="market-trends">
              <h4>Markedsdata</h4>
              <p>Gennemsnitspris per m²: DKK {selectedData.marketTrends.averagePricePerSqm?.toLocaleString()}</p>
              <p>Gennemsnitlig salgstid: {selectedData.marketTrends.averageSellTime} dage</p>
              <p>Prisændring (1 år): {selectedData.marketTrends.priceChange1Year}</p>
            </div>
          )}

          <button onClick={() => handleFetchInformation()} disabled={isFetchingInfo}>
            {isFetchingInfo ? 'Henter information...' : 'Hent information'}
          </button>

          <button onClick={handleEstimatePrice} disabled={isLoading}>
            {isLoading ? 'Beregner...' : 'Beregn pris'}
          </button>

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