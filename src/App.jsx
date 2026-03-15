import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import HomePage from './components/HomePage';
import LeadsPage from './components/LeadsPage';
import './App.css';

function App() {
  const [selectedRole, setSelectedRole] = useState(null);
  const [leads, setLeads] = useState([]);

  useEffect(() => {
    const savedRole = Cookies.get('userRole');
    if (savedRole) {
      setSelectedRole(savedRole);
    }
    
    const savedLeads = Cookies.get('leadsData');
    if (savedLeads) {
      try {
        setLeads(JSON.parse(savedLeads));
      } catch (e) {
        console.error('Ошибка загрузки данных:', e);
      }
    }
  }, []);

  useEffect(() => {
    Cookies.set('leadsData', JSON.stringify(leads), { expires: 7 });
  }, [leads]);

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    Cookies.set('userRole', role, { expires: 7 });
  };

  const handleLogout = () => {
    setSelectedRole(null);
    Cookies.remove('userRole');
  };

  const handleLeadsUpdate = (newLeads) => {
    setLeads(newLeads);
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/" 
          element={
            selectedRole ? (
              <Navigate to="/leads/table" />
            ) : (
              <HomePage onRoleSelect={handleRoleSelect} />
            )
          } 
        />
        <Route 
          path="/leads/:viewMode" 
          element={
            selectedRole ? (
              <LeadsPage 
                role={selectedRole} 
                onLogout={handleLogout}
                leads={leads}
                onLeadsUpdate={handleLeadsUpdate}
              />
            ) : (
              <Navigate to="/" />
            )
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;