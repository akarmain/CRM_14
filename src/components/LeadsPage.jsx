import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function LeadsPage({ role, leads, setLeads, setRole }) {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('table');
  const [showImportModal, setShowImportModal] = useState(false);
  const [importData, setImportData] = useState('');
  const isManager = role.includes('Менеджер');
  const isBoss = role === 'Аналитик' || role === 'Руководитель отдела продаж';
  const visibleLeads = isBoss ? leads : leads.filter(l => l.manager === role);

  const handleImportSubmit = () => {
    const lines = importData.split('\n').filter(l => l.trim());
    const newLeads = lines.map(line => {
      const [id, name, desc, src] = line.split(',').map(s => s.trim());
      return {
        id: id || '-',
        name,
        desc,
        src,
        manager: role,
        uniqueKey: Math.random()
      };
    }).filter(l => l.name);
    setLeads([...leads, ...newLeads]);
    setShowImportModal(false);
    setImportData('');
    alert(`Добавлено: ${newLeads.length}`);
  };

  const handleDeleteLead = (uniqueKey) => {
    if (window.confirm('Удалить эту запись?')) {
      setLeads(leads.filter(l => l.uniqueKey !== uniqueKey));
    }
  };

  const handleClearAll = () => {
    if (window.confirm('Вы уверены, что хотите удалить все свои данные?')) {
      if (isManager) {
        setLeads(leads.filter(l => l.manager !== role));
      } else {
        setLeads([]);
      }
    }
  };

  return (
    <div className="leads-page">
      <div className="top-bar">
        <div className="top-bar-left">
          {isBoss && (
            <>
              <button className="top-bar-button">Отчеты</button>
              <button className="top-bar-button">Экспорт</button>
              <button className="top-bar-button">Запросы</button>
            </>
          )}
        </div>
        <div className="top-bar-right">
          <div className="view-toggle">
            <button 
              className={`view-toggle-button ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              Таблица
            </button>
            <button 
              className={`view-toggle-button ${viewMode === 'kanban' ? 'active' : ''}`}
              onClick={() => setViewMode('kanban')}
            >
              Канбан
            </button>
          </div>
          <button className="role-switch-button" onClick={() => { setRole(null); navigate('/'); }}>
            Сменить роль ({role})
          </button>
        </div>
      </div>

      <div className="leads-content">
        <div className="content-header">
          <h2>Лиды {!isBoss && `(${role})`}</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            {isManager && (
              <>
                <button className="import-button" onClick={() => setShowImportModal(true)}>
                  + Импорт/Ввод данных
                </button>
                {visibleLeads.length > 0 && (
                  <button className="clear-button" onClick={handleClearAll}>
                    Очистить мои лиды
                  </button>
                )}
              </>
            )}
            {isBoss && leads.length > 0 && (
              <button className="clear-button" onClick={handleClearAll}>
                Очистить все лиды
              </button>
            )}
          </div>
        </div>

        {viewMode === 'table' && (
          <div className="table-container">
            <table className="leads-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Название</th>
                  <th>Описание</th>
                  <th>Источник</th>
                  {isBoss && <th>Менеджер</th>}
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {visibleLeads.length > 0 ? (
                  visibleLeads.map(lead => (
                    <tr key={lead.uniqueKey}>
                      <td>{lead.id}</td>
                      <td>{lead.name}</td>
                      <td>{lead.desc}</td>
                      <td>{lead.src}</td>
                      {isBoss && <td>{lead.manager}</td>}
                      <td>
                        <button 
                          className="delete-button"
                          onClick={() => handleDeleteLead(lead.uniqueKey)}
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={isBoss ? 6 : 5} className="empty-table">
                      {isManager ? 'У вас нет лидов' : 'Нет данных для отображения'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {viewMode === 'kanban' && (
          <div className="kanban-placeholder">
            <p>Канбан пуст</p>
          </div>
        )}
      </div>

      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3>Импорт данных для {role}</h3>
            <p className="modal-hint">Введите данные в формате: ID,Название,Описание,Источник</p>
            <p className="modal-example">Пример: 1,Иван Иванов,Клиент,Сайт</p>
            <textarea
              className="import-textarea"
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              rows="8"
              placeholder="Введите данные..."
            />
            <div className="modal-buttons">
              <button className="modal-button cancel" onClick={() => setShowImportModal(false)}>
                Отмена
              </button>
              <button className="modal-button submit" onClick={handleImportSubmit}>
                Импортировать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LeadsPage;