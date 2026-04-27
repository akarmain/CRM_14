import React from 'react';
import { getRoleLabel, getSourceLabel, getStageLabel } from '../lib/leadsApi';
import { formatDateTime } from '../lib/ui';

function LeadHistoryModal({ lead, isLoading = false, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="history-drawer" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>История лида</h3>
            {lead && <p className="muted-copy">#{lead.lead_uid} · {lead.title || 'Без названия'}</p>}
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Закрыть
          </button>
        </div>

        {isLoading ? (
          <div className="modal-section">Загрузка...</div>
        ) : lead ? (
          <div className="history-grid">
            <section className="modal-section">
              <h4>Карточка</h4>
              <dl className="definition-list">
                <div>
                  <dt>Владелец</dt>
                  <dd>{getRoleLabel(lead.owner)}</dd>
                </div>
                <div>
                  <dt>Источник</dt>
                  <dd>{getSourceLabel(lead.source_code)}</dd>
                </div>
                <div>
                  <dt>Текущая стадия</dt>
                  <dd>{getStageLabel(lead.current_stage)}</dd>
                </div>
                <div>
                  <dt>Создан</dt>
                  <dd>{formatDateTime(lead.created_at)}</dd>
                </div>
              </dl>
            </section>

            <section className="modal-section">
              <h4>История стадий</h4>
              <div className="timeline">
                {lead.stage_info.map((item) => (
                  <article key={`${item.stage}-${item.entered_at}`} className="timeline-card">
                    <div className="timeline-header">
                      <strong>{getStageLabel(item.stage)}</strong>
                      <span>{item.approved ? 'approved' : 'pending'}</span>
                    </div>
                    <p>С {formatDateTime(item.entered_at)} до {formatDateTime(item.left_at)}</p>
                    {item.comment.length > 0 && (
                      <div className="timeline-comments">
                        {item.comment.map((comment, index) => (
                          <p key={`${comment.author}-${index}`}>
                            <strong>{getRoleLabel(comment.author)}:</strong> {comment.comment || 'Без комментария'}
                          </p>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>

            <section className="modal-section">
              <h4>Запросы на возврат</h4>
              {lead.return_requests.length === 0 ? (
                <p className="muted-copy">Запросов пока не было.</p>
              ) : (
                <div className="stack-list">
                  {lead.return_requests.map((item) => (
                    <article key={item.id} className="stack-card">
                      <strong>{getStageLabel(item.from_stage)} → {getStageLabel(item.to_stage)}</strong>
                      <p>{item.request_comment}</p>
                      <p className="muted-copy">
                        {getRoleLabel(item.requested_by)} · {formatDateTime(item.requested_at)} · {item.status}
                      </p>
                      {item.review_comment && (
                        <p className="muted-copy">
                          Решение: {item.review_comment} ({item.reviewed_by ? getRoleLabel(item.reviewed_by) : '—'})
                        </p>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="modal-section">
              <h4>Audit log</h4>
              {lead.audit_entries.length === 0 ? (
                <p className="muted-copy">Записей пока нет.</p>
              ) : (
                <div className="stack-list">
                  {lead.audit_entries.map((entry) => (
                    <article key={entry.id} className="stack-card">
                      <strong>{entry.action_type}</strong>
                      <p className="muted-copy">
                        {getRoleLabel(entry.actor_role)} · {formatDateTime(entry.created_at)}
                      </p>
                      <pre className="audit-json">{JSON.stringify(entry.payload_json, null, 2)}</pre>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>
        ) : (
          <div className="modal-section">Нет данных.</div>
        )}
      </div>
    </div>
  );
}

export default LeadHistoryModal;
