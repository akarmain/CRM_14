import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage({ onSelectRole }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();

  const roles = [
    'Менеджер 1',
    'Менеджер 2', 
    'Аналитик',
    'Руководитель отдела продаж'
  ];

  const handleRoleSelect = (role) => {
    onSelectRole(role);
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
            onClick={() => setShowDropdown(!showDropdown)}
          >
            Выбрать роль
          </button>

          {showDropdown && (
            <div className="dropdown-menu">
              {roles.map((role) => (
                <button
                  key={role}
                  className="dropdown-item"
                  onClick={() => handleRoleSelect(role)}
                >
                  {role}
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