import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Severity from './modules/Severity';
import Routing from './modules/Routing';
import Transfer from './modules/Transfer';
import { LayoutDashboard, Map, ArrowLeftRight, Home, Activity } from 'lucide-react';

// App.jsx - Refined Navbar and Layout
const Navbar = () => {
  const location = useLocation();
  if (location.pathname === "/") return null;

  return (
    <nav style={{ 
      display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
      padding: '0 40px', height: '70px', background: '#0f172a', // Darker background
      borderBottom: '1px solid #334155', position: 'sticky', top: 0, zIndex: 1000 
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <Activity color="#ef4444" size={28} />
        <span style={{ fontWeight: 'bold', fontSize: '1.4rem', color: 'white' }}>EMsync HUB</span>
      </div>
      <div style={{ display: 'flex', gap: '15px' }}>
        <Link to="/" style={navBtn}><Home size={18}/> HOME</Link>
        <Link to="/severity" style={navBtn}>SEVERITY</Link>
        <Link to="/routing" style={navBtn}>ROUTING</Link>
        <Link to="/transfer" style={navBtn}>TRANSFER</Link>
      </div>
    </nav>
  );
};

const HomePage = () => (
  <div style={{ width: '100vw', minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '40px', boxSizing: 'border-box' }}>
    <h1 style={{ fontSize: '5rem', marginBottom: '10px', textAlign: 'center', fontWeight: '900' }}>EMsync <span style={{ color: '#ef4444' }}>Command Center</span></h1>
    <p style={{ color: '#94a3b8', fontSize: '1.6rem', marginBottom: '80px', textAlign: 'center' }}>Integrated Emergency Management & Decision Support System</p>
    
    {/* Removed maxWidth to allow full-width expansion */}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '40px', width: '100%' }}>
      <HomeCard to="/severity" title="Severity Analysis" desc="ML-based patient triage and resource prediction." icon={<LayoutDashboard size={80}/>} color="#3b82f6" />
      <HomeCard to="/routing" title="Ambulance Routing" desc="Dynamic GPS tracking and route optimization." icon={<Map size={80}/>} color="#10b981" />
      <HomeCard to="/transfer" title="Secure Transfer" desc="AES-256 encrypted clinical data handoff." icon={<ArrowLeftRight size={80}/>} color="#ef4444" />
    </div>
  </div>
);

const HomeCard = ({ to, title, desc, icon, color }) => (
  <Link to={to} style={{ textDecoration: 'none', background: '#1e293b', padding: '80px 40px', borderRadius: '40px', border: `2px solid #334155`, transition: 'all 0.3s', textAlign: 'center', boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }} className="home-card">
    <div style={{ color: color, marginBottom: '30px' }}>{icon}</div>
    <h2 style={{ color: 'white', fontSize: '2.5rem', marginBottom: '20px' }}>{title}</h2>
    <p style={{ color: '#94a3b8', fontSize: '1.3rem', lineHeight: '1.6' }}>{desc}</p>
  </Link>
);

export default function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', width: '100vw', background: '#0f172a', color: 'white', overflowX: 'hidden' }}>
        <Navbar />
        <main style={{ width: '100%' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/severity" element={<Severity />} />
            <Route path="/routing" element={<Routing />} />
            <Route path="/transfer" element={<Transfer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

const navBtn = { textDecoration: 'none', color: 'white', background: '#334155', padding: '12px 24px', borderRadius: '12px', fontSize: '1.1rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px' };