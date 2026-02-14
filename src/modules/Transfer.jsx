import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { Activity, Bell, ShieldCheck, CheckCircle, Database, RotateCcw, Building, ChevronLeft } from 'lucide-react';

const socket = io('http://127.0.0.1:5000');

// The 12 mandatory emergency service categories
const EMERGENCY_SERVICES = [
  "Cardiac vascular ICU", "Coronary care unit", "Medical ICU", "Medical/Surgical ICU",
  "Neuro Intermediate", "Neuro Surgical ICU", "Surgical ICU", "Trauma Sicu",
  "Ventilator", "Nicu", "Vassopressor", "Dialysis"
];

export default function Transfer() {
  const [hospitals, setHospitals] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [decryptedData, setDecryptedData] = useState(null);
  const [status, setStatus] = useState('System Online');
  const [inputName, setInputName] = useState('');
  const [inputDob, setInputDob] = useState('');
  const [selectedService, setSelectedService] = useState(EMERGENCY_SERVICES[0]);
  const [adminTargetId, setAdminTargetId] = useState(null); 

  useEffect(() => {
    fetchHospitals();
    
    // 1. LISTEN FOR NEW REQUESTS
    socket.on('new_transfer_alert', (data) => {
      setAlerts(prev => [data, ...prev]);
      setStatus('New Incoming Request!');
    });

    // 2. DYNAMIC UPDATE: Triggered on Accept or Manual Override
    socket.on('resource_update', (payload) => {
      fetchHospitals(); // Dynamic refresh for Admin and Registry views
      
      // If the backend sent a reset signal, clear the UI states
      if (payload && payload.status === 'reset') {
        setAlerts([]);
        setDecryptedData(null);
        setStatus('Simulation Reset Complete');
      } else {
        setStatus('Resource Synchronized');
      }
    });

    return () => {
      socket.off('new_transfer_alert');
      socket.off('resource_update');
    };
  }, []);

  const fetchHospitals = () => {
    axios.get('http://127.0.0.1:5000/api/hospitals')
      .then(res => setHospitals(res.data))
      .catch(() => setStatus('Network Error: Check Backend'));
  };

  const handleRequest = (id) => {
    const selectedName = inputName || "Alan Joseph";
    const selectedDob = inputDob || "2004-07-05";

    setStatus(`Requesting ${selectedService}...`);
    
    axios.post('http://127.0.0.1:5000/api/request_transfer', {
      patient_info: { 
        name: selectedName, 
        dob: selectedDob, 
        primary_complaint: "Respiratory Distress",
        age: 21
      },
      vitals: { temp: 38.5, heartrate: 110, o2sat: 88 },
      severity: "Critical",
      destination_id: id,
      requested_service: selectedService 
    }).then(() => setStatus(`Pending: ${selectedName}`));
  };

  const handleAdminUpdate = (hId, service, count) => {
    axios.post('http://127.0.0.1:5000/api/update_beds', { 
      id: hId, 
      service_type: service, 
      count: count 
    });
  };

  // 3. FIXED RESET FUNCTION
  const handleResetSimulation = () => {
    if (window.confirm("Are you sure you want to reset the entire simulation? This will clear all logs and restore resource counts.")) {
      axios.post('http://127.0.0.1:5000/api/reset_simulation')
        .then(() => setStatus('Resetting System...'))
        .catch(() => setStatus('Reset Request Failed'));
    }
  };

  return (
    <div style={{ padding: '40px', backgroundColor: '#0f172a', color: 'white', fontFamily: 'sans-serif' }}>
      
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '50px' }}>
        <div>
          <h1 style={{ fontSize: '3rem', margin: 0 }}>EMsync <span style={{ color: '#ef4444' }}>Command Center</span></h1>
          <div style={{ marginTop: '10px', fontSize: '1.2rem', color: '#94a3b8' }}>STATUS: <strong>{status.toUpperCase()}</strong></div>
        </div>
        {/* Updated Reset Button Call */}
        <button onClick={handleResetSimulation} style={resetBtnStyle}><RotateCcw size={20} /> RESET</button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '25px' }}>
        
        {/* 1. REGISTRY */}
        <div style={cardStyle}>
          <h2 style={{ color: '#3b82f6' }}><Activity /> 1. Registry</h2>
          <div style={inputContainerStyle}>
            <input placeholder="Patient Name" value={inputName} onChange={e => setInputName(e.target.value)} style={inputStyle} />
            <input type="date" value={inputDob} onChange={e => setInputDob(e.target.value)} style={inputStyle} />
            <select value={selectedService} onChange={e => setSelectedService(e.target.value)} style={inputStyle}>
              {EMERGENCY_SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {hospitals.map(h => (
            <div key={h.id} style={listItemStyle}>
              <span>{h.name}</span>
              <button onClick={() => handleRequest(h.id)} style={reqBtnStyle}>Request</button>
            </div>
          ))}
        </div>

        {/* 2. INCOMING */}
        <div style={cardStyle}>
          <h2 style={{ color: '#ef4444' }}><Bell /> 2. Incoming</h2>
          {alerts.map((a, i) => (
            <div key={i} style={alertCardStyle}>
              <strong>{a.hospital_name}</strong>
              <p style={{ margin: '5px 0', fontSize: '0.9rem', color: '#cbd5e1' }}>Service: {a.requested_service}</p>
              <button 
                onClick={() => {
                  axios.post('http://127.0.0.1:5000/api/accept_transfer', { token: a.transfer_id, hospital_id: a.hospital_id })
                  .then(() => axios.post('http://127.0.0.1:5000/api/decrypt', { token: a.transfer_id }))
                  .then(res => setDecryptedData(res.data));
                  setAlerts(alerts.filter((_, idx) => idx !== i));
                }} 
                style={acceptBtnStyle}><CheckCircle size={18} /> ACCEPT</button>
            </div>
          ))}
        </div>

        {/* 3. HANDSHAKE */}
        <div style={cardStyle}>
          <h2 style={{ color: '#10b981' }}><ShieldCheck /> 3. Handshake</h2>
          {decryptedData && (
            <div style={{ animation: 'fadeIn 0.5s' }}>
              <div style={decryptedBoxStyle}>{decryptedData.plain_text}</div>
              <pre style={jsonBoxStyle}>{JSON.stringify(decryptedData.sbar, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* 4. ADMIN VIEW (Dynamic Refresh) */}
        <div style={{ ...cardStyle, border: '2px dashed #475569' }}>
          <h2 style={{ color: '#94a3b8' }}><Database /> 4. Admin View</h2>
          {!adminTargetId ? (
            <div>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '15px' }}>Choose hospital to override counts:</p>
              {hospitals.map(h => (
                <button key={h.id} onClick={() => setAdminTargetId(h.id)} style={adminHospitalBtn}>
                  <Building size={16} /> {h.name}
                </button>
              ))}
            </div>
          ) : (
            <div>
              <button onClick={() => setAdminTargetId(null)} style={backBtnStyle}><ChevronLeft size={16}/> Back</button>
              <h4 style={{ margin: '10px 0', fontSize: '1rem' }}>{hospitals.find(h => h.id === adminTargetId).name}</h4>
              <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '5px' }}>
                {EMERGENCY_SERVICES.map(s => (
                  <div key={s} style={{ marginBottom: '12px' }}>
                    <label style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{s}</label>
                    <input 
                      type="number" 
                      defaultValue={hospitals.find(h => h.id === adminTargetId).services[s] || 0} 
                      onBlur={(e) => handleAdminUpdate(adminTargetId, s, e.target.value)}
                      style={adminInputStyle} 
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// STYLES (No changes here, maintained for completeness)
const cardStyle = { background: '#1e293b', padding: '25px', borderRadius: '25px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' };
const inputContainerStyle = { background: '#0f172a', padding: '15px', borderRadius: '15px', marginBottom: '20px' };
const inputStyle = { width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: 'white', boxSizing: 'border-box' };
const listItemStyle = { display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #334155' };
const reqBtnStyle = { padding: '8px 15px', background: '#3b82f6', border: 'none', color: 'white', borderRadius: '8px', cursor: 'pointer' };
const alertCardStyle = { background: '#2d3748', padding: '15px', borderRadius: '15px', marginBottom: '15px', borderLeft: '8px solid #ef4444' };
const acceptBtnStyle = { width: '100%', padding: '10px', background: '#10b981', border: 'none', color: 'white', fontWeight: 'bold', borderRadius: '10px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '5px' };
const decryptedBoxStyle = { background: '#064e3b', padding: '15px', borderRadius: '12px', marginBottom: '20px', fontSize: '1.2rem', fontWeight: 'bold' };
const jsonBoxStyle = { background: '#000', padding: '15px', borderRadius: '15px', fontSize: '0.8rem', color: '#34d399', overflow: 'auto', maxHeight: '300px' };
const resetBtnStyle = { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: '#475569', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer' };
const adminHospitalBtn = { width: '100%', textAlign: 'left', padding: '12px', background: '#0f172a', color: 'white', border: '1px solid #334155', borderRadius: '10px', marginBottom: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' };
const backBtnStyle = { background: 'none', border: 'none', color: '#ef4444', display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '0.9rem' };
const adminInputStyle = { width: '100%', padding: '8px', background: '#1e293b', border: '1px solid #334155', color: 'white', borderRadius: '6px' };