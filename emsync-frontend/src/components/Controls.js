import React from 'react';

// The component now accepts more props to handle location selection
function Controls({ 
  onStart, 
  onReset, 
  isSimulating, 
  locations, 
  hospitals,
  onStartChange,
  onEndChange
}) {

  // Function to handle the change event from the dropdowns
  const handleSelectChange = (event, handler) => {
    handler(JSON.parse(event.target.value));
  };

  return (
    <div className="sidebar">
      <h1>🚑 EMsync Controls</h1>
      
      {/* --- Location Selection Dropdowns --- */}
      <div className="location-selector">
        <label htmlFor="start-select">Start Location:</label>
        <select 
          id="start-select" 
          onChange={(e) => handleSelectChange(e, onStartChange)}
        >
          {/* Create an <option> for each location in our list */}
          {Object.entries(locations).map(([name, coords]) => (
            <option key={name} value={JSON.stringify(coords)}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <div className="location-selector">
        <label htmlFor="end-select">Destination Hospital:</label>
        <select 
          id="end-select"
          onChange={(e) => handleSelectChange(e, onEndChange)}
        >
          {/* Create an <option> for each hospital in our list */}
          {Object.entries(hospitals).map(([name, coords]) => (
            <option key={name} value={JSON.stringify(coords)}>
              {name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="button-group">
        <button onClick={onStart} disabled={isSimulating}>
          ▶️ Start Simulation
        </button>
        <button onClick={onReset}>⏹️ Reset</button>
      </div>

      {isSimulating && <div className="status-indicator">Simulation in Progress...</div>}
    </div>
  );
}

export default Controls;