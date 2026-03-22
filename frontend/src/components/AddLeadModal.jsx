import React, { useState } from 'react';

const SOURCES = ['Сайт', 'Реклама', 'Рекомендация', 'Событие', 'Другое'];

function AddLeadModal({ onClose, onAdd, isSubmitting }) {
  const [lead, setLead] = useState({
    title: '',
    description: '',
    source: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!lead.title.trim() || !lead.description.trim() || !lead.source.trim()) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    await onAdd({
      title: lead.title,
      description: lead.description,
      source: lead.source,
    });
  };

  return (
    <div className="modal-overlay" onClick={isSubmitting ? undefined : onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Добавить нового лида</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Название:</label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={lead.title}
              onChange={(e) => setLead({...lead, title: e.target.value})}
              placeholder="Введите название"
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Описание:</label>
            <textarea
              id="description"
              className="form-textarea"
              value={lead.description}
              onChange={(e) => setLead({...lead, description: e.target.value})}
              placeholder="Введите описание"
              rows="3"
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="source">Источник:</label>
            <select
              id="source"
              className="form-select"
              value={lead.source}
              onChange={(e) => setLead({...lead, source: e.target.value})}
              disabled={isSubmitting}
            >
              <option value="">Выберите источник</option>
              {SOURCES.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>

          <div className="modal-buttons">
            <button type="button" className="modal-button cancel" onClick={onClose} disabled={isSubmitting}>
              Отмена
            </button>
            <button type="submit" className="modal-button submit" disabled={isSubmitting}>
              {isSubmitting ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddLeadModal;
