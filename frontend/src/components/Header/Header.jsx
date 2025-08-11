import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { forwardGeocode } from '../../api/mapbox';
import './Header.css';

function Header({ mode, onSearchSelect }) {
  const { theme, toggleTheme, isDark, isTransitioning } = useTheme();
  const [addressInput, setAddressInput] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (mode === 'free' && addressInput.length > 2) {
      setIsSearching(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const features = await forwardGeocode(addressInput + ' Denmark');
          const filteredFeatures = features.filter(feature => {
            const placeType = feature.place_type || [];
            const placeName = feature.place_name || '';
            return placeType.includes('address') && /\d+/.test(placeName) && !placeType.includes('poi');
          });
          setSearchResults(filteredFeatures.slice(0, 5));
          setShowDropdown(filteredFeatures.length > 0);
        } catch (error) {
          console.error('Search error:', error);
          setSearchResults([]);
          setShowDropdown(false);
        } finally {
          setIsSearching(false);
        }
      }, 300);
    } else {
      setSearchResults([]);
      setShowDropdown(false);
      setIsSearching(false);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [addressInput, mode]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectResult = (result) => {
    setAddressInput(result.place_name);
    setShowDropdown(false);
    setSearchResults([]);
    onSearchSelect(result);
  };

  return (
    <header className="app-header" data-theme={theme}>
      <div className="header-content">
        <h1 className="header-title">Bolig Beregner</h1>
        
        {mode === 'free' && (
          <div className="search-container" ref={dropdownRef}>
            <div className="search-input-container">
              <input
                type="text"
                placeholder="Søg på en adresse i Danmark..."
                value={addressInput}
                onChange={e => setAddressInput(e.target.value)}
                onFocus={() => setShowDropdown(searchResults.length > 0)}
                className="address-input"
              />
              {isSearching && <div className="search-spinner">🔄</div>}
            </div>
            
            {showDropdown && searchResults.length > 0 && (
              <div className="search-dropdown">
                {searchResults.map((result) => (
                  <div
                    key={result.id}
                    className="search-result-item"
                    onClick={() => handleSelectResult(result)}
                  >
                    {result.place_name}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="header-controls">
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            disabled={isTransitioning}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          >
            {isTransitioning ? (
              <span className="theme-icon">🔄</span>
            ) : isDark ? (
              <span className="theme-icon">☀️</span>
            ) : (
              <span className="theme-icon">🌙</span>
            )}
            <span className="theme-text">
              {isDark ? 'Light' : 'Dark'} Mode
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;