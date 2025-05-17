import React from 'react'
import './Start.css'

function Start({ onEnterFree }) {
  return (
    <div className="start-container">
      <h1 className="start-title">Bolig beregner</h1>
      <button className="start-button" onClick={onEnterFree}>
        Enter Free Mode
      </button>
    </div>
  )
}

export default Start
