import React, { useState } from 'react';

function ImportModal({ role, onClose, onImport }) {
  const [importData, setImportData] = useState('');

  const generateUniqueId = () => {
    return Date.now() + Math.random().toString(36).substr(2, 9);
  };

  const handleImport = () => {
    if (!importData.trim()) {
      alert('Введите данные для импорта');
      return;
    }

    const lines = importData.trim().split('\n');
    
    const newLeads = lines.map(line => {
      const [id, name, description, source] = line.split(',').map(item => item.trim());
      return {
        customId: id || '',
        name: name || '',
        description: description || '',
        source: source || '',
        manager: role,
        status: 'Новый',
        uniqueKey: generateUniqueId()
      };
    }).filter(lead => lead.customId && lead.name);

    if (newLeads.length > 0) {
      onImport(newLeads);
    } else {
      alert('Нет корректных данных для импорта');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Импорт данных через CSV</h3>
        <p className="modal-hint">Введите данные в формате: ID,Название,Описание,Источник</p>
        <p className="modal-example">Пример: 1,Иван Петров,Клиент из Москвы,Сайт</p>
        <textarea
          className="import-textarea"
          value={importData}
          onChange={(e) => setImportData(e.target.value)}
          rows="8"
          placeholder="Введите данные..."
        />
        <div className="modal-buttons">
          <button className="modal-button cancel" onClick={onClose}>
            Отмена
          </button>
          <button className="modal-button submit" onClick={handleImport}>
            Импортировать
          </button>
        </div>
      </div>
    </div>
  );
}

export default ImportModal;