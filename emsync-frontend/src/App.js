import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import L from 'leaflet';
import "leaflet/dist/leaflet.css";
import axios from 'axios';
import './App.css';
import Controls from './components/Controls';

// Fix for default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// --- API Communication Function ---
const fetchRouteData = async (start, end) => {
  try {
    const response = await axios.post('http://127.0.0.1:5000/api/get_route', { start, end });
    const decoded = response.data.decoded_route;
    const summary = response.data.routes[0].summary;
    return { route: decoded, duration: summary.duration }; // Return both route and duration
  } catch (error) {
    console.error("Error fetching route:", error);
    return null;
  }
};

function App() {
  // --- Location Data ---
  const locations = {
    "Varapuzha": [76.2828, 10.0815],
    "Edappally": [76.3115, 10.0248],
    "Kaloor": [76.2996, 9.9984],
  };
  const hospitals = {
    "Aster Medcity": [76.27745, 10.04348],
    "Lourdes Hospital": [76.27742, 10.00668],
    "Amrita Hospital": [76.29250, 10.03264],
  };

  // --- State Management ---
  const [startPoint, setStartPoint] = useState(locations.Varapuzha);
  const [endPoint, setEndPoint] = useState(hospitals["Aster Medcity"]);
  const [route, setRoute] = useState([]);
  const [routeDuration, setRouteDuration] = useState(0);
  const [ambulancePosition, setAmbulancePosition] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [rerouteMessage, setRerouteMessage] = useState("");
  const animationRef = useRef(null);

  // --- Initial Route Fetch ---
  useEffect(() => {
    const getInitialRoute = async () => {
      setIsSimulating(false);
      const data = await fetchRouteData(startPoint, endPoint);
      if (data) {
        setRoute(data.route);
        setRouteDuration(data.duration);
        setAmbulancePosition(data.route[0]);
      }
    };
    getInitialRoute();
  }, [startPoint, endPoint]);

  // --- Animation & Dynamic Re-routing ---
  useEffect(() => {
    if (isSimulating && route.length > 0) {
      let currentIndex = 0;
      let elapsedTime = 0;

      animationRef.current = setInterval(async () => {
        // Move ambulance
        if (currentIndex < route.length - 1) {
          currentIndex++;
          setAmbulancePosition(route[currentIndex]);
          elapsedTime += 0.5; // Each tick simulates 0.5s
        } else {
          setIsSimulating(false);
          return;
        }

        // Dynamic Re-routing every 10 seconds (100 ticks * 50ms)
        if (currentIndex % 100 === 0) {
          const currentAmbPosition = [route[currentIndex][1], route[currentIndex][0]]; // lon, lat
          const newData = await fetchRouteData(currentAmbPosition, endPoint);

          if (newData) {
            const remainingOldDuration = routeDuration - elapsedTime;
            if (newData.duration < remainingOldDuration - 30) {
              setRerouteMessage("Faster route found! Re-routing...");
              setTimeout(() => setRerouteMessage(""), 3000);

              setRoute(newData.route);
              setRouteDuration(newData.duration);
              currentIndex = 0;
              elapsedTime = 0;
            }
          }
        }
      }, 50);
    } else {
      clearInterval(animationRef.current);
    }
    return () => clearInterval(animationRef.current);
  }, [isSimulating, route, endPoint, routeDuration]);

  // --- Simulation Controls ---
  const startSimulation = () => {
    if (route.length > 0) {
      setAmbulancePosition(route[0]);
      setIsSimulating(true);
      setRerouteMessage("");
    }
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    if (route.length > 0) setAmbulancePosition(route[0]);
  };

  if (route.length === 0) return <div>Loading...</div>;
  const position = [startPoint[1], startPoint[0]];

  return (
    <div className="App">
      <Controls
        onStart={startSimulation}
        onReset={resetSimulation}
        isSimulating={isSimulating}
        locations={locations}
        hospitals={hospitals}
        onStartChange={setStartPoint}
        onEndChange={setEndPoint}
      />
      {rerouteMessage && <div className="reroute-banner">{rerouteMessage}</div>}
      <div className="map-container">
        <MapContainer center={position} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <Polyline positions={route} color="blue" />
          <Marker position={[startPoint[1], startPoint[0]]}><Popup>Start</Popup></Marker>
          <Marker position={[endPoint[1], endPoint[0]]}><Popup>Destination</Popup></Marker>
          {ambulancePosition && (
            <Marker
              position={ambulancePosition}
              icon={L.divIcon({ className: 'ambulance-icon', html: '🚑' })}
            >
              <Popup>Ambulance</Popup>
            </Marker>
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
