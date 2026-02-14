import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import L from 'leaflet';
import "leaflet/dist/leaflet.css";
import axios from 'axios';
import Controls from '../components/Controls.jsx';

// Fix for default marker icon issue in Vite environment
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

export default function Routing() {
  /* ---------------- DATA ---------------- */
  const locations = {
    Varapuzha: [76.2828, 10.0815],
    Edappally: [76.3115, 10.0248],
    Kaloor: [76.2996, 9.9984],
  };

  const hospitals = {
    "Aster Medcity": [76.27745, 10.04348],
    "Lourdes Hospital": [76.27742, 10.00668],
    "Amrita Hospital": [76.29250, 10.03264],
  };

  /* ---------------- STATE ---------------- */
  const [startPoint, setStartPoint] = useState(locations.Varapuzha);
  const [endPoint, setEndPoint] = useState(hospitals["Aster Medcity"]);
  const [route, setRoute] = useState([]);
  const [ambulancePosition, setAmbulancePosition] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const animationRef = useRef(null);

  /* ---------------- INITIAL ROUTE ---------------- */
  useEffect(() => {
    const loadRoute = async () => {
      setIsSimulating(false);
      try {
        const res = await axios.post('http://127.0.0.1:6005/api/get_route', { 
            start: startPoint, 
            end: endPoint 
        });
        // Your backend already returns [lat, lng] in decoded_route
        const path = res.data.decoded_route;
        setRoute(path);
        setAmbulancePosition(path[0]);
      } catch (err) {
        console.error("Route fetch failed", err);
      }
    };
    loadRoute();
  }, [startPoint, endPoint]);

  /* ---------------- SIMULATION ---------------- */
  useEffect(() => {
    if (!isSimulating || route.length === 0) return;

    let index = 0;
    animationRef.current = setInterval(() => {
      if (index < route.length - 1) {
        index++;
        setAmbulancePosition(route[index]);
      } else {
        setIsSimulating(false);
        clearInterval(animationRef.current);
      }
    }, 50);

    return () => clearInterval(animationRef.current);
  }, [isSimulating, route]);

  /* ---------------- UI ---------------- */
  return (
    <div style={{ height: 'calc(100vh - 70px)', width: '100vw', position: 'relative' }}>
      {/* Floating UI Controls */}
      <div style={{ 
        position: 'absolute', 
        top: '20px', 
        left: '20px', 
        zIndex: 1000, 
        background: 'rgba(30, 41, 59, 0.9)', 
        padding: '20px', 
        borderRadius: '20px', 
        border: '1px solid #334155',
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
      }}>
        <Controls
          onStart={() => setIsSimulating(true)}
          onReset={() => { setIsSimulating(false); setAmbulancePosition(route[0]); }}
          isSimulating={isSimulating}
          locations={locations}
          hospitals={hospitals}
          onStartChange={setStartPoint}
          onEndChange={setEndPoint}
        />
      </div>

      {/* Full Screen Map Container */}
      <MapContainer
        center={[startPoint[1], startPoint[0]]} // Leaflet marker needs [lat, lng]
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Path rendering using direct route coordinates from your Postman test */}
        <Polyline positions={route} color="#3b82f6" weight={6} opacity={0.8} />

        <Marker position={[startPoint[1], startPoint[0]]}><Popup>Start</Popup></Marker>
        <Marker position={[endPoint[1], endPoint[0]]}><Popup>Destination</Popup></Marker>

        {ambulancePosition && (
          <Marker
            position={ambulancePosition}
            icon={L.divIcon({ html: `<div style="
    font-size: 35px; 
    display: flex; 
    justify-content: center; 
    align-items: center;
    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.8));
    line-height: 1;
    transform: translate(-5px, -10px);
  ">🚑</div>`, className: 'amb-icon', iconSize: [10, 10],iconAnchor: [5, 5] })}
          >
            <Popup>Ambulance</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}