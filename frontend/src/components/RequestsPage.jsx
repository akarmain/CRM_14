import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../auth/SessionProvider';
import {
  approveReturnRequest,
  fetchReturnRequests,
  getRoleLabel,
  getStageLabel,
  rejectReturnRequest,
} from '../lib/leadsApi';
import { formatDateTime } from '../lib/ui';

function RequestsPage() {
  const navigate = useNavigate();
  const { session, logout } = useSession();
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [reviewComments, setReviewComments] = useState({});

  const loadRequests = async () => {
    setIsLoading(true);
    setError('');
    try {
      const payload = await fetchReturnRequests({ status: 'pending' });
      setItems(payload);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadRequests();
  }, []);

  const reviewRequest = async (item, action) => {
    const comment = reviewComments[item.id]?.trim();
    if (!comment) {
      setError('Для approve/reject нужен комментарий РОП.');
      return;
    }
    setError('');
    try {
      if (action === 'approve') {
        await approveReturnRequest(item.id, comment);
      } else {
        await rejectReturnRequest(item.id, comment);
      }
      await loadRequests();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  return (
    <div className="leads-page">
      <div className="top-bar">
        <div className="top-bar-left">
          <button className="top-bar-button" onClick={() => navigate('/leads/table')}>
            Лиды
          </button>
          <button className="top-bar-button" onClick={() => navigate('/reports')}>
            Отчёты
          </button>
        </div>
        <div className="top-bar-right">
          <button className="role-switch-button" onClick={logout}>
            Сменить роль ({getRoleLabel(session.role)})
          </button>
        </div>
      </div>

      <div className="leads-content">
        <div className="content-header">
          <div>
            <h2>Очередь возвратов</h2>
            <p className="page-subtitle">
              Заявки менеджеров на возврат лида на предыдущую стадию.
            </p>
          </div>
        </div>

        {error && <p className="error-banner">{error}</p>}

        <main className="content-panel stack-gap">
          {isLoading ? (
            <div className="panel-card empty-panel">
              <p className="muted-copy">Загрузка заявок...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="panel-card empty-panel">
              <p className="muted-copy">Открытых заявок на возврат нет.</p>
            </div>
          ) : (
            <div className="stack-list">
              {items.map((item) => (
                <article key={item.id} className="request-card">
                  <div className="request-header">
                    <div>
                      <strong>Лид #{item.lead_uid || item.lead_id}</strong>
                      <p className="muted-copy">
                        {getStageLabel(item.from_stage)} → {getStageLabel(item.to_stage)}
                      </p>
                    </div>
                    <span className="status-pill">{item.status}</span>
                  </div>
                  <p>{item.request_comment}</p>
                  <p className="muted-copy">
                    {getRoleLabel(item.requested_by)} · {formatDateTime(item.requested_at)}
                  </p>
                  <label className="field">
                    <span>Комментарий РОП</span>
                    <textarea
                      rows={3}
                      value={reviewComments[item.id] ?? ''}
                      onChange={(event) =>
                        setReviewComments((current) => ({
                          ...current,
                          [item.id]: event.target.value,
                        }))
                      }
                      placeholder="Почему вы одобряете или отклоняете возврат"
                    />
                  </label>
                  <div className="inline-actions">
                    <button className="primary-button" onClick={() => reviewRequest(item, 'approve')}>
                      Одобрить
                    </button>
                    <button className="danger-button" onClick={() => reviewRequest(item, 'reject')}>
                      Отклонить
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default RequestsPage;
