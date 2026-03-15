import React from 'react';

function LeadsTable({ leads, isBoss, isManager, onDelete }) {
  return (
    <div className="table-container">
      <table className="leads-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Описание</th>
            <th>Источник</th>
            <th>Статус</th>
            {isBoss && <th>Менеджер</th>}
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {leads.length > 0 ? (
            leads.map((lead) => (
              <tr key={lead.uniqueKey}>
                <td>{lead.customId}</td>
                <td>{lead.name}</td>
                <td>{lead.description}</td>
                <td>{lead.source}</td>
                <td>
                  <span className="status-text">{lead.status || 'Новый'}</span>
                </td>
                {isBoss && <td>{lead.manager}</td>}
                <td>
                  <button 
                    className="delete-button"
                    onClick={() => onDelete(lead.uniqueKey)}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={isBoss ? 7 : 6} className="empty-table">
                {isManager ? 'У вас нет лидов' : 'Нет данных для отображения'}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default LeadsTable;