import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { getBuildingDetails, getPropertyHistory, estimatePrice } from '../../api/backend';
import './Free.css';

const Free = forwardRef(({ map }, ref) => {
  if (!map) return null;

  const [selectedData, setSelectedData] = useState(null);
  const [estimatedPrice, setEstimatedPrice] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingInfo, setIsFetchingInfo] = useState(false);
  const [visible, setVisible] = useState(true);

  // Expose the handleLocationSelect function to the parent component (App.jsx)
  useImperativeHandle(ref, () => ({
    handleLocationSelect
  }));

  // This function is called from App.jsx when a search result is selected in the Header
  const handleLocationSelect = (result) => {
    const [lng, lat] = result.center;

    map.flyTo({ center: [lng, lat], zoom: 18, pitch: 60, essential: true });

    const selectedDataObj = {
      address: result.place_name || result.address,
      salesHistory: []
    };
    setSelectedData(selectedDataObj);
    setVisible(true); // Ensure the overlay is visible when a location is selected
    setEstimatedPrice(null); // Clear any previous price estimate

    // Fetch property information after a short delay to allow the map to animate
    setTimeout(() => {
      handleFetchInformation(selectedDataObj);
    }, 500);
  };

  async function handleFetchInformation(dataOverride = null) {
    const currentData = dataOverride || selectedData;

    if (!currentData || !currentData.address) return;

    setIsFetchingInfo(true);
    try {
      const [buildingInfo, historyData] = await Promise.all([
        getBuildingDetails(null, currentData.address),
        getPropertyHistory(currentData.address, currentData.zip)
      ]);

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
      };

      setSelectedData(updatedData);

    } catch (error) {
      console.error('Error fetching information:', error);
      alert('Fejl ved hentning af information');
    } finally {
      setIsFetchingInfo(false);
    }
  }

  async function handleEstimatePrice() {
    if (!selectedData) return;

    setIsLoading(true);
    try {
      const estimate = await estimatePrice(selectedData);
      setEstimatedPrice(estimate);
    } catch (error) {
      console.error('Error estimating price:', error);
      alert('Fejl ved prisberegning');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="free-controls">
      {selectedData && visible && ( 
        <div className="select-overlay">
            <button className="close-button" onClick={() => setVisible(false)}>
        ×
      </button>
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

          <h4 className='text'>Salgshistorik</h4>
          <ul>
            {selectedData.salesHistory?.map((sale, i) => (
              <li className='text' key={i}>
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
  );
});

Free.displayName = 'Free';

export default Free;