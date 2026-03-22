import React from 'react';

const STATUSES = ['Новый', 'В работе', 'Потерянный', 'Завершенный'];

function LeadsKanban({ leads, isBoss, isAnalyst, onDelete, onStatusChange }) {
  const leadsByStatus = {};
  STATUSES.forEach(status => {
    leadsByStatus[status] = leads.filter(l => l.status === status);
  });

  const handleDragStart = (e, leadKey) => {
    if (!isAnalyst) {
      e.dataTransfer.setData('leadKey', leadKey);
    }
  };

  const handleDrop = (e, status) => {
    e.preventDefault();
    if (isAnalyst) return;
    const leadKey = e.dataTransfer.getData('leadKey');
    onStatusChange(leadKey, status);
  };

  const handleDragOver = (e) => {
    if (!isAnalyst) {
      e.preventDefault();
    }
  };

  return (
    <div className="kanban-container">
      {STATUSES.map(status => (
        <div
          key={status}
          className="kanban-column"
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, status)}
        >
          <h3>{status}</h3>
          {leadsByStatus[status].map(lead => (
            <div
              key={lead.uniqueKey}
              className={`kanban-card ${isAnalyst ? 'readonly' : ''}`}
              draggable={!isAnalyst}
              onDragStart={(e) => handleDragStart(e, lead.uniqueKey)}
            >
              <div className="kanban-card-header">
                <span className="kanban-card-id">ID: {lead.customId}</span>
                {isBoss && <span className="kanban-card-manager">{lead.manager}</span>}
              </div>
              <h4>{lead.name}</h4>
              <p>{lead.description}</p>
              <div className="kanban-card-footer">
                <span className="kanban-card-source">{lead.source}</span>
                <button className="delete-button-small" onClick={() => onDelete(lead.uniqueKey)}>
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default LeadsKanban;