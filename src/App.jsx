import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import HomePage from './components/HomePage';
import LeadsPage from './components/LeadsPage';
import './App.css';

function App() {
  const [role, setRole] = useState(null);
  const [leads, setLeads] = useState([]);

  useEffect(() => {
    const savedRole = Cookies.get('role');
    const savedLeads = Cookies.get('leads');
    
    if (savedRole) setRole(savedRole);
    if (savedLeads) setLeads(JSON.parse(savedLeads));
  }, []);


  useEffect(() => {
    if (role) Cookies.set('role', role);
    if (leads.length) Cookies.set('leads', JSON.stringify(leads));
  }, [role, leads]);

  return (
    <Router>
      <Routes>
        <Route path="/" element={
          role ? <Navigate to="/leads" /> : <HomePage onSelectRole={setRole} />
        } />
        <Route path="/leads" element={
          role ? <LeadsPage role={role} leads={leads} setLeads={setLeads} setRole={setRole} /> 
                : <Navigate to="/" />
        } />
      </Routes>
    </Router>
  );
}

export default App;