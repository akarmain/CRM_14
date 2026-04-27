import React, { useState } from 'react';

function ImportModal({ isSubmitting = false, onClose, onSubmit }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError('Выберите CSV или XLSX файл.');
      return;
    }

    setError('');
    await onSubmit(file);
  };

  return (
    <div className="modal-overlay" onClick={isSubmitting ? undefined : onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>Импорт лидов</h3>
          <button type="button" className="ghost-button" onClick={onClose} disabled={isSubmitting}>
            Закрыть
          </button>
        </div>
        <form className="modal-form" onSubmit={handleSubmit}>
          <p className="muted-copy">
            Поддерживаются файлы <code>.csv</code> и <code>.xlsx</code>. Для менеджера
            владелец будет назначен автоматически, для РОП поле <code>owner</code> в файле
            сохраняется.
          </p>
          <label className="upload-card">
            <span>{file ? file.name : 'Выбрать файл'}</span>
            <input
              type="file"
              accept=".csv,.xlsx"
              disabled={isSubmitting}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          {error && <p className="error-banner">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={onClose} disabled={isSubmitting}>
              Отмена
            </button>
            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? 'Импортируем...' : 'Импортировать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ImportModal;
