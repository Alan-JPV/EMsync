import React from 'react';

const Severity = () => {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <iframe 
        src="http://localhost:8501/?embed=true" 
        style={{ width: '100%', height: '90vh', border: 'none', borderRadius: '15px' }} 
        title="Severity Dashboard"
      />
    </div>
  );
};

export default Severity;