import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../auth/SessionProvider';
import {
  exportLeads,
  fetchReportsSummary,
  getRoleLabel,
  getStageLabel,
  OWNER_OPTIONS,
  SOURCE_OPTIONS,
} from '../lib/leadsApi';
import { downloadBlob, formatDurationHours } from '../lib/ui';

function ReportsPage() {
  const navigate = useNavigate();
  const { session, logout } = useSession();
  const [filters, setFilters] = useState({
    owner: '',
    source_code: '',
    date_from: '',
    date_to: '',
  });
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadSummary = async () => {
    setIsLoading(true);
    setError('');
    try {
      const payload = await fetchReportsSummary(filters);
      setSummary(payload);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadSummary();
  }, [filters.owner, filters.source_code, filters.date_from, filters.date_to]);

  const handleExport = async (format) => {
    try {
      const { blob, filename } = await exportLeads(format, { owner: filters.owner });
      downloadBlob(blob, filename);
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
          {session.role === 'sales_head' && (
            <button className="top-bar-button" onClick={() => navigate('/requests')}>
              Запросы
            </button>
          )}
        </div>
        <div className="top-bar-right">
          <button className="top-bar-button" onClick={() => handleExport('csv')}>
            Экспорт CSV
          </button>
          <button className="top-bar-button" onClick={() => handleExport('xlsx')}>
            Экспорт Excel
          </button>
          <button className="role-switch-button" onClick={logout}>
            Сменить роль ({getRoleLabel(session.role)})
          </button>
        </div>
      </div>

      <div className="leads-content">
        <div className="content-header">
          <div>
            <h2>Отчёты</h2>
            <p className="page-subtitle">
              Конверсии, длительность стадий и выгрузка данных.
            </p>
          </div>
        </div>

        <section className="filters-bar">
          <label className="field compact-field">
            <span>Владелец</span>
            <select
              value={filters.owner}
              onChange={(event) => setFilters((current) => ({ ...current, owner: event.target.value }))}
            >
              <option value="">Все</option>
              {OWNER_OPTIONS.map((owner) => (
                <option key={owner.value} value={owner.value}>
                  {owner.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field compact-field">
            <span>Источник</span>
            <select
              value={filters.source_code}
              onChange={(event) =>
                setFilters((current) => ({ ...current, source_code: event.target.value }))
              }
            >
              <option value="">Все</option>
              {SOURCE_OPTIONS.map((source) => (
                <option key={source.value} value={source.value}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field compact-field">
            <span>С даты</span>
            <input
              type="date"
              value={filters.date_from}
              onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value }))}
            />
          </label>
          <label className="field compact-field">
            <span>По дату</span>
            <input
              type="date"
              value={filters.date_to}
              onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value }))}
            />
          </label>
        </section>

        {error && <p className="error-banner">{error}</p>}

        <main className="content-panel stack-gap">
          {isLoading ? (
            <div className="panel-card empty-panel">
              <p className="muted-copy">Считаем метрики...</p>
            </div>
          ) : summary ? (
            <>
              <section className="metrics-grid">
                <article className="metric-card">
                  <span>Всего лидов</span>
                  <strong>{summary.total_leads}</strong>
                </article>
                {summary.counts.map((item) => (
                  <article key={item.stage} className="metric-card">
                    <span>{getStageLabel(item.stage)}</span>
                    <strong>{item.count}</strong>
                  </article>
                ))}
              </section>

              <section className="split-grid">
                <article className="panel-card">
                  <h3>Конверсии</h3>
                  <table className="simple-table">
                    <thead>
                      <tr>
                        <th>Переход</th>
                        <th>Из</th>
                        <th>В</th>
                        <th>Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.conversions.map((item) => (
                        <tr key={`${item.from_stage}-${item.to_stage}`}>
                          <td>{getStageLabel(item.from_stage)} → {getStageLabel(item.to_stage)}</td>
                          <td>{item.from_count}</td>
                          <td>{item.to_count}</td>
                          <td>{item.rate}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </article>

                <article className="panel-card">
                  <h3>Средняя длительность стадии</h3>
                  <table className="simple-table">
                    <thead>
                      <tr>
                        <th>Стадия</th>
                        <th>Часы</th>
                        <th>Секунды</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.average_stage_durations.map((item) => (
                        <tr key={item.stage}>
                          <td>{getStageLabel(item.stage)}</td>
                          <td>{formatDurationHours(item.average_hours)}</td>
                          <td>{item.average_seconds}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </article>
              </section>
            </>
          ) : null}
        </main>
      </div>
    </div>
  );
}

export default ReportsPage;
