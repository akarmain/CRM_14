import React, { useState } from 'react';

function AddLeadModal({ role, onClose, onAdd }) {
  const [lead, setLead] = useState({
    id: '',
    name: '',
    description: '',
    source: ''
  });

  const generateUniqueId = () => {
    return Date.now() + Math.random().toString(36).substr(2, 9);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!lead.id.trim() || !lead.name.trim() || !lead.description.trim() || !lead.source.trim()) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    onAdd({
      customId: lead.id,
      name: lead.name,
      description: lead.description,
      source: lead.source,
      manager: role,
      status: 'Новый',
      uniqueKey: generateUniqueId()
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Добавить нового лида</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="id">ID:</label>
            <input
              type="text"
              id="id"
              className="form-input"
              value={lead.id}
              onChange={(e) => setLead({...lead, id: e.target.value})}
              placeholder="Введите ID"
            />
          </div>

          <div className="form-group">
            <label htmlFor="name">Название:</label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={lead.name}
              onChange={(e) => setLead({...lead, name: e.target.value})}
              placeholder="Введите название"
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
            />
          </div>

          <div className="form-group">
            <label htmlFor="source">Источник:</label>
            <select
              id="source"
              className="form-select"
              value={lead.source}
              onChange={(e) => setLead({...lead, source: e.target.value})}
            >
              <option value="">Выберите источник</option>
              <option value="Сайт">Сайт</option>
              <option value="Телефон">Телефон</option>
              <option value="Почта">Почта</option>
              <option value="Мессенджер">Мессенджер</option>
              <option value="Соцсети">Соцсети</option>
              <option value="Рекомендация">Рекомендация</option>
            </select>
          </div>

          <div className="modal-buttons">
            <button type="button" className="modal-button cancel" onClick={onClose}>
              Отмена
            </button>
            <button type="submit" className="modal-button submit">
              Добавить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddLeadModal;