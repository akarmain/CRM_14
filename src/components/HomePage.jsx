import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage({ onRoleSelect }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();

  const roles = [
    { id: 1, name: 'Менеджер 1', path: 'manager1' },
    { id: 2, name: 'Менеджер 2', path: 'manager2' },
    { id: 3, name: 'Аналитик', path: 'analyst' },
    { id: 4, name: 'Руководитель отдела продаж', path: 'director' }
  ];

  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  const handleRoleSelect = (role) => {
    onRoleSelect(role.name);
    setShowDropdown(false);
    navigate('/leads');
  };

  return (
    <div className="home-container">
      <header className="header">
        <h1>CRM 14</h1>
        <p className="subtitle">пробная версия</p>
      </header>

      <main className="main">
        <div className="button-container">
          <button 
            className="primary-button"
            onClick={toggleDropdown}
          >
            Выбрать роль
          </button>

          {showDropdown && (
            <div className="dropdown-menu">
              {roles.map((role) => (
                <button
                  key={role.id}
                  className="dropdown-item"
                  onClick={() => handleRoleSelect(role)}
                >
                  {role.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default HomePage;