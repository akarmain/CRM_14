import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import HomePage from './components/HomePage';
import LeadsPage from './components/LeadsPage';
import {
  createLead,
  createLeadsBatch,
  fetchLeads,
  getLeadIds,
  moveLeadStage,
  removeLead,
} from './lib/leadsApi';
import './App.css';

function App() {
  const [selectedRole, setSelectedRole] = useState(() => Cookies.get('userRole') ?? null);
  const [leads, setLeads] = useState([]);
  const [isLoadingLeads, setIsLoadingLeads] = useState(false);
  const [leadsError, setLeadsError] = useState('');

  useEffect(() => {
    if (!selectedRole) {
      setLeads([]);
      setLeadsError('');
      return;
    }

    let isActive = true;

    async function loadLeads() {
      setIsLoadingLeads(true);
      setLeadsError('');

      try {
        const loadedLeads = await fetchLeads();
        if (isActive) {
          setLeads(loadedLeads);
        }
      } catch (error) {
        if (isActive) {
          setLeadsError(error.message);
        }
      } finally {
        if (isActive) {
          setIsLoadingLeads(false);
        }
      }
    }

    loadLeads();

    return () => {
      isActive = false;
    };
  }, [selectedRole]);

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    Cookies.set('userRole', role, { expires: 7 });
  };

  const handleLogout = () => {
    setSelectedRole(null);
    Cookies.remove('userRole');
    setLeads([]);
  };

  const handleLeadCreate = async (lead) => {
    const createdLead = await createLead(lead, selectedRole);
    setLeads((current) => [...current, createdLead]);
    return createdLead;
  };

  const handleLeadsImport = async (leadsToCreate) => {
    const createdLeads = await createLeadsBatch(leadsToCreate, selectedRole);
    setLeads((current) => [...current, ...createdLeads]);
    return createdLeads;
  };

  const handleLeadDelete = async (leadUid) => {
    await removeLead(leadUid);
    setLeads((current) => current.filter((lead) => lead.leadUid !== leadUid));
  };

  const handleLeadsClear = async (leadsToDelete) => {
    const leadIds = getLeadIds(leadsToDelete);

    for (const leadId of leadIds) {
      await removeLead(leadId);
    }

    setLeads((current) => current.filter((lead) => !leadIds.includes(lead.leadUid)));
  };

  const handleLeadStatusChange = async (leadUid, status) => {
    const updatedLead = await moveLeadStage(leadUid, status, selectedRole);
    setLeads((current) =>
      current.map((lead) => (lead.leadUid === leadUid ? updatedLead : lead))
    );
    return updatedLead;
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
        <Route path="/leads" element={<Navigate to="/leads/table" replace />} />
        <Route 
          path="/leads/:viewMode" 
          element={
            selectedRole ? (
              <LeadsPage 
                role={selectedRole} 
                onLogout={handleLogout}
                leads={leads}
                isLoading={isLoadingLeads}
                error={leadsError}
                onLeadCreate={handleLeadCreate}
                onLeadsImport={handleLeadsImport}
                onLeadDelete={handleLeadDelete}
                onLeadsClear={handleLeadsClear}
                onLeadStatusChange={handleLeadStatusChange}
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
