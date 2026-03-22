import React, { useState } from 'react';

function ImportModal({ onClose, onImport, isSubmitting }) {
  const [importData, setImportData] = useState('');

  const handleImport = async () => {
    if (!importData.trim()) {
      alert('Введите данные для импорта');
      return;
    }

    const lines = importData.trim().split('\n');
    
    const newLeads = lines.map(line => {
      const parts = line.split(',').map(item => item.trim());
      const [title, description, source] = parts.length >= 4 ? parts.slice(1, 4) : parts;

      return {
        title: title || '',
        description: description || '',
        source: source || '',
      };
    }).filter(lead => lead.title && lead.source);

    if (newLeads.length > 0) {
      await onImport(newLeads);
    } else {
      alert('Нет корректных данных для импорта');
    }
  };

  return (
    <div className="modal-overlay" onClick={isSubmitting ? undefined : onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Импорт данных через CSV</h3>
        <p className="modal-hint">Введите данные в формате: Название,Описание,Источник</p>
        <p className="modal-example">Или в старом формате: ID,Название,Описание,Источник</p>
        <p className="modal-example">Пример: Компания А,Клиент из Москвы,Сайт</p>
        <textarea
          className="import-textarea"
          value={importData}
          onChange={(e) => setImportData(e.target.value)}
          rows="8"
          placeholder="Введите данные..."
          disabled={isSubmitting}
        />
        <div className="modal-buttons">
          <button className="modal-button cancel" onClick={onClose} disabled={isSubmitting}>
            Отмена
          </button>
          <button className="modal-button submit" onClick={handleImport} disabled={isSubmitting}>
            {isSubmitting ? 'Импорт...' : 'Импортировать'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ImportModal;
