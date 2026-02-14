import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { Activity, Bell, ShieldCheck, CheckCircle, Database, RotateCcw } from 'lucide-react';

const socket = io('http://127.0.0.1:5000');

// Randomized patient pool for dynamic simulation
const mockPatients = [
  { name: "Alan", dob: "1995-05-12", age: 30, complaint: "Severe Respiratory Distress" },
  { name: "Abhijith", dob: "1998-11-20", age: 27, complaint: "Acute Cardiac Symptoms" },
  { name: "Batman", dob: "1939-05-27", age: 86, complaint: "Multiple Blunt Force Trauma" },
  { name: "Spiderman", dob: "1962-08-10", age: 63, complaint: "Toxic Venom Exposure" },
  { name: "Luffy", dob: "1997-07-22", age: 28, complaint: "Extreme Dehydration & Exhaustion" }
];

export default function Transfer() {
  const [hospitals, setHospitals] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [decryptedData, setDecryptedData] = useState(null);
  const [status, setStatus] = useState('System Online');
  const [inputName, setInputName] = useState(''); // Line 21
  const [inputDob, setInputDob] = useState('');   // Line 22

  useEffect(() => {
    fetchHospitals();
    
    // Listen for new transfer alerts from backend
    socket.on('new_transfer_alert', (data) => {
      setAlerts(prev => [data, ...prev]);
      setStatus('New Incoming Request!');
    });

    // Listen for bed count updates or system resets
    socket.on('resource_update', () => {
      fetchHospitals();
      setDecryptedData(null); 
      setStatus('Registry Updated');
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

  const handleManualUpdate = (id, val) => {
    axios.post('http://127.0.0.1:5000/api/update_beds', { id, beds: val });
  };

  const handleReset = () => {
    if (window.confirm("Reset entire simulation and clear all logs?")) {
      axios.post('http://127.0.0.1:5000/api/reset_simulation')
        .then(() => {
          setAlerts([]);
          setDecryptedData(null);
          setStatus('System Reset Complete');
        });
    }
  };

/* const handleRequest = (id) => {
    // Pick a random patient from the list
    const patient = mockPatients[Math.floor(Math.random() * mockPatients.length)];
    
    setStatus(`Sending Request for ${patient.name}...`);
    
    axios.post('http://127.0.0.1:5000/api/request_transfer', {
      patient_info: { 
        name: patient.name, 
        dob: patient.dob, 
        primary_complaint: patient.complaint,
        age: patient.age 
      },
      vitals: { 
        temp: (37 + Math.random() * 3).toFixed(1), 
        heartrate: Math.floor(90 + Math.random() * 50), 
        o2sat: Math.floor(80 + Math.random() * 15) 
      },
      severity: Math.random() > 0.5 ? "Critical" : "Urgent",
      destination_id: id
    }).then(() => setStatus(`Pending: ${patient.name}`));
  };*/

  /*const handleRequest = (id) => {
  // Define randomized patient pool
  const mockPatients = [
    { name: "Alan", dob: "1995-05-12", age: 30, complaint: "Severe Respiratory Distress" },
    { name: "Abhijith", dob: "1998-11-20", age: 27, complaint: "Acute Cardiac Symptoms" },
    { name: "Batman", dob: "1939-05-27", age: 86, complaint: "Multiple Blunt Force Trauma" },
    { name: "Spiderman", dob: "1962-08-10", age: 63, complaint: "Toxic Venom Exposure" },
    { name: "Luffy", dob: "1997-07-22", age: 28, complaint: "Extreme Dehydration & Exhaustion" }
  ];

  // Pick a random patient
  const patient = mockPatients[Math.floor(Math.random() * mockPatients.length)];
  
  setStatus(`Sending Request for ${patient.name}...`);
  
  axios.post('http://127.0.0.1:5000/api/request_transfer', {
    patient_info: { 
      name: patient.name, 
      dob: patient.dob, 
      primary_complaint: patient.complaint,
      age: patient.age 
    },
    vitals: { 
      // Generate numeric vitals to avoid server-side TypeErrors
      temp: parseFloat((37 + Math.random() * 3).toFixed(1)), 
      heartrate: Math.floor(90 + Math.random() * 50), 
      o2sat: Math.floor(82 + Math.random() * 15) 
    },
    severity: Math.random() > 0.5 ? "Critical" : "Urgent",
    destination_id: id
  }).then(() => setStatus(`Request Pending for ${patient.name}`));
};*/
const handleRequest = (id) => {
    const names = ["Alan", "Abhijith", "Batman", "Spiderman", "Luffy"];
    
    // Use manual inputs if available, else pick random
    const selectedName = inputName || names[Math.floor(Math.random() * names.length)];
    const selectedDob = inputDob || "1995-05-15";

    setStatus(`Sending Request for ${selectedName}...`);
    
    axios.post('http://127.0.0.1:5000/api/request_transfer', {
      patient_info: { 
        name: selectedName, 
        dob: selectedDob, 
        primary_complaint: "Respiratory Distress",
        age: Math.floor(25 + Math.random() * 40)
      },
      vitals: { 
        temp: parseFloat((37 + Math.random() * 3).toFixed(1)), 
        heartrate: Math.floor(90 + Math.random() * 50), 
        o2sat: Math.floor(82 + Math.random() * 15) 
      },
      severity: Math.random() > 0.5 ? "Critical" : "Urgent",
      destination_id: id
    }).then(() => setStatus(`Request Pending: ${selectedName}`));
  };

  const handleAccept = (token, hospitalId, index) => {
    setStatus('Committing Bed...');
    axios.post('http://127.0.0.1:5000/api/accept_transfer', { token, hospital_id: hospitalId })
      .then(() => {
        // Fetch and show decrypted identity and SBAR automatically
        axios.post('http://127.0.0.1:5000/api/decrypt', { token })
          .then(res => setDecryptedData(res.data));
        
        setAlerts(alerts.filter((_, i) => i !== index));
        setStatus('Transfer Accepted & Bed Reserved');
      });
  };

  return (
    <div style={{ padding: '40px', backgroundColor: '#0f172a', minHeight: 'auto', color: 'white', fontFamily: 'sans-serif' }}>
      
      {/* HEADER SECTION */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '50px' }}>
        <div>
          <h1 style={{ fontSize: '3.5rem', margin: 0, borderBottom: '5px solid #ef4444', display: 'inline-block' }}>
            EMsync <span style={{ color: '#ef4444' }}>Command Center</span>
          </h1>
          <div style={{ marginTop: '10px', fontSize: '1.2rem', color: '#94a3b8' }}>
            STATUS: <strong style={{ color: '#3b82f6' }}>{status.toUpperCase()}</strong>
          </div>
        </div>
        
        <button 
          onClick={handleReset} 
          style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '15px 30px', background: '#475569', color: 'white', border: 'none', borderRadius: '15px', cursor: 'pointer', fontSize: '1.2rem', transition: '0.3s' }}>
          <RotateCcw size={24} /> RESET SIMULATION
        </button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '30px' }}>
        
        {/* 1. PARAMEDIC VIEW / REGISTRY 
        <div style={{ background: '#1e293b', padding: '30px', borderRadius: '25px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: '2rem', color: '#3b82f6', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Activity size={32} /> 1. Registry
          </h2>
          {hospitals.map(h => (
            <div key={h.id} style={{ padding: '20px 0', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{h.name}</span><br/>
                <span style={{ fontSize: '1.2rem' }}>Beds: <b style={{ color: h.available_beds > 0 ? '#10b981' : '#ef4444' }}>{h.available_beds}</b></span>
              </div>
              <button 
                onClick={() => handleRequest(h.id)} 
                disabled={h.available_beds <= 0}
                style={{ padding: '10px 20px', fontSize: '1.1rem', backgroundColor: h.available_beds > 0 ? '#3b82f6' : '#475569', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer' }}>
                Request
              </button>
            </div>
          ))}
        </div>
        */}
        {/* 1. PARAMEDIC VIEW / REGISTRY */}
        <div style={{ background: '#1e293b', padding: '30px', borderRadius: '25px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: '2rem', color: '#3b82f6', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Activity size={32} /> 1. Registry
          </h2>

          {/* MANUAL INPUT BOX */}
          <div style={{ marginBottom: '20px', padding: '20px', background: '#0f172a', borderRadius: '15px', border: '1px solid #334155' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#94a3b8', fontSize: '1rem' }}>MANUAL PATIENT ENTRY</h4>
            <input 
              placeholder="Patient Name" 
              value={inputName} 
              onChange={(e) => setInputName(e.target.value)} 
              style={{ width: '90%', padding: '12px', marginBottom: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: 'white', fontSize: '1rem' }}
            />
            <input 
              type="date" 
              value={inputDob} 
              onChange={(e) => setInputDob(e.target.value)} 
              style={{ width: '90%', padding: '12px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: 'white', fontSize: '1rem' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
               <p style={{ fontSize: '0.75rem', color: '#475569', margin: 0 }}>* Blank uses random data.</p>
               {(inputName || inputDob) && (
                 <button onClick={() => {setInputName(''); setInputDob('');}} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem' }}>Clear Fields</button>
               )}
            </div>
          </div>

          {/* HOSPITAL LIST (RESTORED BUTTONS) */}
          {hospitals.map(h => (
            <div key={h.id} style={{ padding: '20px 0', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{h.name}</span><br/>
                <span style={{ fontSize: '1.2rem' }}>Beds: <b style={{ color: h.available_beds > 0 ? '#10b981' : '#ef4444' }}>{h.available_beds}</b></span>
              </div>
              <button 
                onClick={() => handleRequest(h.id)} 
                disabled={h.available_beds <= 0}
                style={{ padding: '10px 20px', fontSize: '1.1rem', backgroundColor: h.available_beds > 0 ? '#3b82f6' : '#475569', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer' }}>
                Request
              </button>
            </div>
          ))}
        </div>
        {/* 2. HOSPITAL ALERTS / INCOMING */}
        <div style={{ background: '#1e293b', padding: '30px', borderRadius: '25px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: '2rem', color: '#ef4444', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Bell size={32} /> 2. Incoming
          </h2>
          {alerts.length === 0 && <p style={{ fontSize: '1.2rem', color: '#64748b', textAlign: 'center', marginTop: '40px' }}>Waiting for requests...</p>}
          {alerts.map((a, i) => (
            <div key={i} style={{ padding: '25px', background: '#2d3748', borderRadius: '20px', marginBottom: '25px', borderLeft: '10px solid #ef4444' }}>
              <strong style={{ fontSize: '1.3rem' }}>For: {a.hospital_name}</strong>
              <div style={{ wordBreak: 'break-all', fontSize: '0.85rem', margin: '15px 0', color: '#94a3b8', background: '#000', padding: '10px', borderRadius: '8px', border: '1px solid #334155' }}>
                <span style={{color: '#ef4444', fontWeight: 'bold'}}>AES-256 TOKEN ID:</span><br/>{a.transfer_id}
              </div>
              <button 
                onClick={() => handleAccept(a.transfer_id, a.hospital_id, i)} 
                style={{ width: '100%', padding: '15px', background: '#10b981', border: 'none', color: 'white', fontSize: '1.2rem', fontWeight: 'bold', borderRadius: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <CheckCircle size={24} /> ACCEPT & COMMIT
              </button>
            </div>
          ))}
        </div>

        {/* 3. SECURITY / HANDSHAKE VIEW */}
        <div style={{ background: '#1e293b', padding: '30px', borderRadius: '25px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: '2rem', color: '#10b981', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <ShieldCheck size={32} /> 3. Handshake
          </h2>
          {!decryptedData ? (
            <div style={{ textAlign: 'center', marginTop: '40px', color: '#64748b' }}>
              <p style={{ fontSize: '1.2rem' }}>Waiting for digital commit...</p>
            </div>
          ) : (
            <div style={{ animation: 'fadeIn 0.5s' }}>
              <div style={{ background: '#064e3b', padding: '20px', borderRadius: '15px', marginBottom: '25px', border: '2px solid #10b981' }}>
                <h4 style={{ margin: 0, color: '#34d399', fontSize: '1rem' }}>DECRYPTED IDENTITY:</h4>
                <p style={{ fontSize: '1.6rem', fontWeight: 'bold', margin: '10px 0' }}>{decryptedData.plain_text}</p>
              </div>
              <h4 style={{ color: '#94a3b8', fontSize: '1rem' }}>SBAR PACKET (JSON):</h4>
              <pre style={{ background: '#000', padding: '15px', borderRadius: '15px', fontSize: '0.9rem', overflow: 'auto', maxHeight: '350px', color: '#34d399', border: '1px solid #334155' }}>
                {JSON.stringify(decryptedData.sbar, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* 4. ADMIN VIEW / MANUAL CONTROL */}
        <div style={{ background: '#1e293b', padding: '30px', borderRadius: '25px', border: '2px dashed #475569' }}>
          <h2 style={{ fontSize: '2rem', color: '#94a3b8', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Database size={32} /> 4. Admin View
          </h2>
          <p style={{fontSize: '0.9rem', color: '#64748b', marginBottom: '20px'}}>Direct Database Overrides</p>
          {hospitals.map(h => (
            <div key={h.id} style={{ marginBottom: '20px', padding: '15px', background: '#0f172a', borderRadius: '15px' }}>
              <div style={{marginBottom: '10px', fontSize: '1.1rem'}}>{h.name}</div>
              <input 
                type="number" 
                defaultValue={h.available_beds} 
                onBlur={(e) => handleManualUpdate(h.id, e.target.value)}
                style={{ width: '100%', padding: '12px', borderRadius: '10px', background: '#1e293b', color: 'white', border: '1px solid #334155', fontSize: '1.1rem' }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}