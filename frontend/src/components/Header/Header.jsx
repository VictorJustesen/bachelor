import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import './Header.css';

function Header() {
  const { theme, toggleTheme, isDark, isTransitioning } = useTheme();

  return (
    <header className="app-header" data-theme={theme}>
      <div className="header-content">
        <h1 className="header-title">Bolig Beregner</h1>
        
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
