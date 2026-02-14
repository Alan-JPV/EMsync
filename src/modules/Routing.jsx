import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import { Clock, Navigation, AlertTriangle, MapPin, Lock, Unlock, Building2, Play, RotateCcw } from 'lucide-react';

// REQUIRED: Assets & Leaflet CSS
import 'leaflet/dist/leaflet.css';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix for default marker icon in Vite
let DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Custom Symbols (Ambulance and Waypoints)
const ambulanceIcon = L.divIcon({
  html: `<div style="font-size: 38px; filter: drop-shadow(0 0 8px rgba(255,255,255,0.9));">🚑</div>`,
  className: 'amb-icon',
  iconSize: [45, 45],
  iconAnchor: [22, 22]
});

export default function Routing() {
  const hospitals = {
    "Aster Medcity": [76.27745, 10.04348],
    "Lourdes Hospital": [76.27742, 10.00668],
    "Amrita Hospital": [76.29250, 10.03264],
  };

  const [startPoint, setStartPoint] = useState([76.2828, 10.0815]); 
  const [selectedHospital, setSelectedHospital] = useState("Aster Medcity");
  const [route, setRoute] = useState([]);
  const [navData, setNavData] = useState({ duration: 0, distance: 0, steps: [], density: [] });
  
  const [isLocked, setIsLocked] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [ambPos, setAmbPos] = useState(null);
  const [currentStepIdx, setCurrentStepIdx] = useState(-1);
  const animationRef = useRef(null);

  function MapClickHandler() {
    useMapEvents({ click: (e) => { if (!isLocked && !isSimulating) setStartPoint([e.latlng.lng, e.latlng.lat]); } });
    return null;
  }

  useEffect(() => {
    const loadRoute = async () => {
      try {
        const res = await axios.post('http://localhost:6005/api/get_route', { 
          start: startPoint, end: hospitals[selectedHospital] 
        });
        setRoute(res.data.decoded_route);
        setAmbPos(res.data.decoded_route[0]);
        setNavData({
          duration: Math.ceil(res.data.duration / 60),
          distance: (res.data.distance / 1000).toFixed(1),
          steps: res.data.steps,
          density: res.data.density_zones
        });
      } catch (err) { console.error("API Error", err); }
    };
    loadRoute();
  }, [startPoint, selectedHospital]);

  // Simulation Logic (Reduced Speed: 100ms interval)
  useEffect(() => {
    if (!isSimulating || route.length === 0) return;

    let index = 0;
    animationRef.current = setInterval(() => {
      if (index < route.length - 1) {
        index++;
        setAmbPos(route[index]);
        
        const foundStep = navData.steps.findIndex(s => s.way_points[0] <= index && s.way_points[1] >= index);
        if (foundStep !== -1) setCurrentStepIdx(foundStep);
      } else {
        setIsSimulating(false);
        clearInterval(animationRef.current);
      }
    }, 100); 

    return () => clearInterval(animationRef.current);
  }, [isSimulating, route]);

  const handleReset = () => {
    setIsSimulating(false);
    clearInterval(animationRef.current);
    setAmbPos(route[0]);
    setCurrentStepIdx(-1);
  };

  return (
    <div style={{ height: 'calc(100vh - 70px)', width: '100vw', display: 'flex', background: '#0f172a', overflow: 'hidden' }}>
      
      {/* SIDEBAR: Configuration only */}
      <div style={sidebarStyle}>
        <div style={headerStyle}>
          <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Smart Routing</h2>
          <button onClick={() => setIsLocked(!isLocked)} style={{ ...lockBtn, background: isLocked ? '#ef4444' : '#334155' }}>
            {isLocked ? <Lock size={18} /> : <Unlock size={18} />}
          </button>
        </div>

        <div style={{ opacity: isLocked ? 0.5 : 1, marginBottom: '20px' }}>
          <label style={labelStyle}><Building2 size={14}/> Hospital</label>
          <select disabled={isLocked || isSimulating} value={selectedHospital} onChange={(e) => setSelectedHospital(e.target.value)} style={dropdownStyle}>
            {Object.keys(hospitals).map(name => <option key={name} value={name}>{name}</option>)}
          </select>
        </div>

        <div style={statGrid}>
          <div style={statItem}><Clock size={16} color="#10b981"/> <strong>{navData.duration}m</strong></div>
          <div style={statItem}><MapPin size={16} color="#3b82f6"/> <strong>{navData.distance}km</strong></div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setIsSimulating(true)} disabled={isSimulating} style={actionBtn}><Play size={16}/> Start</button>
          <button onClick={handleReset} style={{...actionBtn, background: '#475569'}}><RotateCcw size={16}/> Reset</button>
        </div>
      </div>

      {/* MAP AREA */}
      <div style={{ flex: 1, position: 'relative' }}>
        
        {/* FLOATING HUD (Google Maps Style) */}
        {isSimulating && currentStepIdx !== -1 && (
          <div style={floatingNavBox}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px', color: '#3b82f6', marginBottom: '8px'}}>
              <Navigation size={22} />
              <span style={{fontWeight: 'bold', fontSize: '1.2rem'}}>Navigation</span>
            </div>
            <p style={{margin: 0, fontSize: '1.1rem', fontWeight: '500'}}>{navData.steps[currentStepIdx].instruction}</p>
            <div style={{marginTop: '12px', color: '#94a3b8', fontSize: '0.9rem'}}>
              {navData.steps[currentStepIdx].distance}m until next turn
            </div>
          </div>
        )}

        <MapContainer center={[startPoint[1], startPoint[0]]} zoom={13} style={{ height: "100%", width: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MapClickHandler />
          
          {/* Main Path: High Opacity */}
          <Polyline positions={route} color="#3b82f6" weight={7} opacity={0.9} />
          
          {/* Traffic Density: Orange Overlay */}
          {navData.density.map((zone, i) => (
            <Polyline 
              key={i} 
              positions={route.slice(zone.start, zone.end + 1)} 
              color="#f97316" 
              weight={10} 
              opacity={1}
            />
          ))}
          
          <Marker position={[startPoint[1], startPoint[0]]}><Popup>Emergency Point</Popup></Marker>
          <Marker position={[hospitals[selectedHospital][1], hospitals[selectedHospital][0]]}><Popup>{selectedHospital}</Popup></Marker>

          {ambPos && <Marker position={ambPos} icon={ambulanceIcon} />}
        </MapContainer>
      </div>
    </div>
  );
}

// STYLES
const sidebarStyle = { width: '380px', background: '#1e293b', padding: '25px', display: 'flex', flexDirection: 'column', borderRight: '1px solid #334155' };
const headerStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' };
const lockBtn = { border: 'none', color: 'white', padding: '10px', borderRadius: '10px', cursor: 'pointer' };
const dropdownStyle = { width: '100%', padding: '12px', background: '#0f172a', color: 'white', border: '1px solid #334155', borderRadius: '10px' };
const labelStyle = { color: '#94a3b8', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '8px' };
const statGrid = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' };
const statItem = { background: '#0f172a', padding: '15px', borderRadius: '12px', textAlign: 'center' };
const actionBtn = { flex: 1, padding: '12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontWeight: 'bold' };

const floatingNavBox = { 
  position: 'absolute', top: '25px', right: '25px', zIndex: 1000, width: '340px', 
  background: 'rgba(15, 23, 42, 0.95)', backdropFilter: 'blur(10px)',
  padding: '24px', borderRadius: '24px', border: '1px solid #3b82f6',
  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
};