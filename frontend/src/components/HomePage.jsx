import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../auth/SessionProvider';
import { ROLE_OPTIONS } from '../lib/leadsApi';

function HomePage() {
  const navigate = useNavigate();
  const { selectRole } = useSession();
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleRoleSelect = async (role) => {
    setIsSubmitting(true);
    setError('');
    setShowDropdown(false);
    try {
      await selectRole(role);
      navigate('/leads/table');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="home-container">
      <header className="header">
        <h1>CRM 14</h1>
        <p className="subtitle">пробная версия</p>
      </header>

      <main className="main">
        <div className="button-container">
          {error && <p className="error-banner">{error}</p>}
          <button
            className="primary-button"
            onClick={() => setShowDropdown((current) => !current)}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Подключаем роль...' : 'Выбрать роль'}
          </button>

          {showDropdown && (
            <div className="dropdown-menu">
              {ROLE_OPTIONS.map((role) => (
                <button
                  key={role.value}
                  className="dropdown-item"
                  onClick={() => handleRoleSelect(role.value)}
                  disabled={isSubmitting}
                >
                  {role.label}
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
