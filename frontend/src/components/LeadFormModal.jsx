import React, { useEffect, useState } from 'react';
import { OWNER_OPTIONS, SOURCE_OPTIONS } from '../lib/leadsApi';

function LeadFormModal({
  mode = 'create',
  initialLead = null,
  canManageOwner = false,
  isSubmitting = false,
  onClose,
  onSubmit,
}) {
  const [form, setForm] = useState({
    title: '',
    notes: '',
    source_code: 'website',
    owner: 'manager_1',
  });

  useEffect(() => {
    if (initialLead) {
      setForm({
        title: initialLead.title ?? '',
        notes: initialLead.notes ?? '',
        source_code: initialLead.source_code ?? 'website',
        owner: initialLead.owner ?? 'manager_1',
      });
      return;
    }
    setForm({
      title: '',
      notes: '',
      source_code: 'website',
      owner: 'manager_1',
    });
  }, [initialLead]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) {
      return;
    }

    const payload = {
      title: form.title.trim(),
      notes: form.notes.trim() || null,
      source_code: form.source_code,
    };
    if (canManageOwner) {
      payload.owner = form.owner;
    }
    await onSubmit(payload);
  };

  return (
    <div className="modal-overlay" onClick={isSubmitting ? undefined : onClose}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>{mode === 'edit' ? 'Редактировать лид' : 'Добавить лид'}</h3>
          <button type="button" className="ghost-button" onClick={onClose} disabled={isSubmitting}>
            Закрыть
          </button>
        </div>
        <form className="modal-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Название</span>
            <input
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              disabled={isSubmitting}
              placeholder="Например, ГК Север"
            />
          </label>
          <label className="field">
            <span>Комментарий</span>
            <textarea
              value={form.notes}
              onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
              disabled={isSubmitting}
              rows={4}
              placeholder="Контекст, детали, договорённости"
            />
          </label>
          <label className="field">
            <span>Источник</span>
            <select
              value={form.source_code}
              onChange={(event) => setForm((current) => ({ ...current, source_code: event.target.value }))}
              disabled={isSubmitting}
            >
              {SOURCE_OPTIONS.map((source) => (
                <option key={source.value} value={source.value}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>
          {canManageOwner && (
            <label className="field">
              <span>Владелец</span>
              <select
                value={form.owner}
                onChange={(event) => setForm((current) => ({ ...current, owner: event.target.value }))}
                disabled={isSubmitting}
              >
                {OWNER_OPTIONS.map((owner) => (
                  <option key={owner.value} value={owner.value}>
                    {owner.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={onClose} disabled={isSubmitting}>
              Отмена
            </button>
            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? 'Сохраняем...' : mode === 'edit' ? 'Сохранить' : 'Создать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default LeadFormModal;
