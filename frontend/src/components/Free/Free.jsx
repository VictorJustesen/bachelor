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

  // 👇 EXTRACT ZIP FROM ADDRESS
  const address = result.place_name || result.address;
  const zipMatch = address.match(/\b\d{4}\b/); // Extract 4-digit postal code
  const extractedZip = zipMatch ? zipMatch[0] : null;

  const selectedDataObj = {
    address: address,
    zip: extractedZip,  // 👈 ADD THIS!
    salesHistory: []
  };
  
  setSelectedData(selectedDataObj);
  setVisible(true);
  setEstimatedPrice(null);

  setTimeout(() => {
    handleFetchInformation(selectedDataObj);
  }, 500);
};
  async function handleFetchInformation(dataOverride = null) {
    const currentData = dataOverride || selectedData;

    if (!currentData || !currentData.address) return;

    setIsFetchingInfo(true);
    try {
      // Get building info
      const buildingInfo = await getBuildingDetails(null, currentData.address);

      // Get property history (NEW)
      let salesHistory = [];
      try {
        const historyResponse = await getPropertyHistory(currentData.address, currentData.zip);
        salesHistory = historyResponse.salesHistory || [];
      } catch (err) {
        console.warn('No sales history found:', err);
      }

      // Merge both results
      const updatedData = {
        ...currentData,
        ...buildingInfo,
        salesHistory, // Use the history from the endpoint
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
    // Wait for state to update (if user just changed input)
    await new Promise(resolve => setTimeout(resolve, 50));
    const latestData = selectedData; // Now should be up-to-date

    // Map frontend fields to backend expected fields
    const mappedData = {
      ...latestData,
      m2: latestData.sqm,         // Map 'sqm' to 'm2'
      'Vær.': latestData.rooms,      // Map 'rooms' to 'Vær'
      postnummer: latestData.zip, // Map 'zip' to 'postnummer'
      // You can add more mappings here if needed
    };

    console.log('🚀 Sending ALL DATA to prediction service:', mappedData);
    const estimate = await estimatePrice(mappedData);
    setEstimatedPrice(estimate);
  } catch (error) {
    console.error('❌ Error estimating price:', error);
    alert(`Fejl ved prisberegning: ${error.message}`);
  } finally {
    setIsLoading(false);
  }
}

  const buildingTypes = [
    'Villa',
    'Ejerlejlighed',
    'Rækkehus',
    'Fritidshus',
    'Landejendom'
  ];

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
            Antal rum:
            <input
              type="number"
              value={selectedData.rooms || ''}
              onChange={e => setSelectedData({ ...selectedData, rooms: +e.target.value })}
            />
          </label>
          {/*<label>
            Byggeår:
            <input
              type="number"
              value={selectedData.year || ''}
              onChange={e => setSelectedData({ ...selectedData, year: +e.target.value })}
            />
          </label>*/}
          <label>
            Bygningstype:
            <select className="text"
              value={selectedData.buildingType || ''}
              onChange={e => {
                const val = e.target.value;
                // Set all one-hot fields to 0, except the selected one
                const oneHot = {};
                buildingTypes.forEach(type => {
                  oneHot[`btype_${type}`] = type === val ? 1 : 0;
                });
                setSelectedData({
                  ...selectedData,
                  buildingType: val,
                  btype: val,
                  ...oneHot
                });
              }}
            >
              <option className="text" value="">Vælg type</option>
              {buildingTypes.map(type => (
                <option key={type} className="text" value={type}>{type}</option>
              ))}
            </select>
          </label>
          {selectedData.salesHistory && selectedData.salesHistory.length > 0 && (
            <>
              <h4 className='text'>Salgshistorik</h4>
              <ul>
                {selectedData.salesHistory?.map((sale, i) => (
                  <li className='text' key={i}>
                    {sale.date}: DKK {sale.price?.toLocaleString()} {sale.type && `(${sale.type})`}
              </li>
            ))}
          </ul>

            </>
          )}
          {selectedData.mean_of_5_neighbors_pris_pr_m2 && selectedData.pris_pr_m2_mean_365D_postnummer && (
            <div className="market-trends">
              <h4 style={{ margin: '0' }} className='text'>Markedsdata</h4>
              <p className="text">Gennemsnitspris pr m² blandt dine naboer: {(Math.round(selectedData.mean_of_5_neighbors_pris_pr_m2) || 0).toLocaleString()} Kr</p>
              <p className="text">Gennemsnitspris pr m² i kommunen: KR {(Math.round(selectedData.pris_pr_m2_mean_365D_postnummer) || 0).toLocaleString()} Kr </p>



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
              <h4 className="text">Estimeret pris:</h4>
              <p className="price-value">DKK {(Math.round(estimatedPrice.estimated_price) || 0).toLocaleString()}</p>
              {/*

              {estimatedPrice.confidence_score && (
                <p className="confidence">Tillid: {(estimatedPrice.confidence_score * 100).toFixed(1)}%</p>
              )}*/}
              {estimatedPrice.model_version && (
                <p className="model-info">Model: XGBoost</p>
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