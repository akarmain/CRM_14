import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSession } from '../auth/SessionProvider';
import {
  createLead,
  deleteLead,
  exportLeads,
  fetchLeadDetail,
  fetchLeads,
  getRoleLabel,
  importLeads,
  moveLeadStage,
  OWNER_OPTIONS,
  requestReturnToPreviousStage,
  SOURCE_OPTIONS,
  updateLead,
} from '../lib/leadsApi';
import { downloadBlob } from '../lib/ui';
import ImportModal from './ImportModal';
import LeadFormModal from './LeadFormModal';
import LeadHistoryModal from './LeadHistoryModal';
import LeadsKanban from './LeadsKanban';
import LeadsTable from './LeadsTable';

function LeadsPage() {
  const navigate = useNavigate();
  const { viewMode = 'table' } = useParams();
  const { session, logout } = useSession();
  const [leads, setLeads] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    owner: '',
    source_code: '',
    date_from: '',
    date_to: '',
  });
  const [leadFormState, setLeadFormState] = useState({ open: false, mode: 'create', lead: null });
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [historyState, setHistoryState] = useState({ open: false, lead: null, isLoading: false });

  const permissions = session.permissions;
  const isSalesHead = session.role === 'sales_head';
  const isManager = session.role === 'manager_1' || session.role === 'manager_2';

  const activeView = viewMode === 'kanban' ? 'kanban' : 'table';

  const loadLeads = async () => {
    setIsLoading(true);
    setError('');
    try {
      const nextLeads = await fetchLeads(
        permissions.can_read_all_leads ? filters : {}
      );
      setLeads(nextLeads);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadLeads();
  }, [session.role, filters.owner, filters.source_code, filters.date_from, filters.date_to]);

  const refreshHistory = async (leadUid) => {
    setHistoryState({ open: true, lead: null, isLoading: true });
    try {
      const detail = await fetchLeadDetail(leadUid);
      setHistoryState({ open: true, lead: detail, isLoading: false });
    } catch (requestError) {
      setHistoryState({ open: false, lead: null, isLoading: false });
      setError(requestError.message);
    }
  };

  const runMutation = async (handler) => {
    setIsMutating(true);
    setError('');
    try {
      await handler();
      await loadLeads();
      if (historyState.open && historyState.lead?.lead_uid) {
        await refreshHistory(historyState.lead.lead_uid);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsMutating(false);
    }
  };

  const handleLeadSubmit = async (payload) => {
    await runMutation(async () => {
      if (leadFormState.mode === 'edit' && leadFormState.lead) {
        await updateLead(leadFormState.lead.lead_uid, payload);
      } else {
        await createLead(payload);
      }
      setLeadFormState({ open: false, mode: 'create', lead: null });
    });
  };

  const handleImportSubmit = async (file) => {
    await runMutation(async () => {
      await importLeads(file);
      setIsImportOpen(false);
    });
  };

  const handleMoveStage = async (lead, targetStage) => {
    if (lead.current_stage === targetStage) {
      return;
    }
    const rawComment = window.prompt('Комментарий к смене стадии (необязательно):', '') ?? '';
    await runMutation(async () => {
      await moveLeadStage(lead.lead_uid, targetStage, rawComment.trim() || null);
    });
  };

  const handleRequestReturn = async (lead) => {
    const comment = window.prompt('Почему нужно вернуть лид на предыдущую стадию?');
    if (!comment || !comment.trim()) {
      return;
    }
    await runMutation(async () => {
      await requestReturnToPreviousStage(lead.lead_uid, comment.trim());
    });
  };

  const handleDelete = async (lead) => {
    if (!window.confirm(`Удалить лид ${lead.lead_uid}?`)) {
      return;
    }
    await runMutation(async () => {
      await deleteLead(lead.lead_uid);
    });
  };

  const handleExport = async (format) => {
    try {
      const { blob, filename } = await exportLeads(format, permissions.can_read_all_leads ? { owner: filters.owner } : {});
      downloadBlob(blob, filename);
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  const filterControls = useMemo(() => (
    <div className="filters-bar">
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
    </div>
  ), [filters]);

  return (
    <div className="leads-page">
      <div className="top-bar">
        <div className="top-bar-left">
          {permissions.can_view_reports && (
            <button className="top-bar-button" onClick={() => navigate('/reports')}>
              Отчёты
            </button>
          )}
          {permissions.can_export_leads && (
            <>
              <button className="top-bar-button" onClick={() => handleExport('csv')}>
                Экспорт CSV
              </button>
              <button className="top-bar-button" onClick={() => handleExport('xlsx')}>
                Экспорт Excel
              </button>
            </>
          )}
          {permissions.can_review_returns && (
            <button className="top-bar-button" onClick={() => navigate('/requests')}>
              Запросы
            </button>
          )}
        </div>
        <div className="top-bar-right">
          <div className="view-toggle">
            <button
              className={`view-toggle-button ${activeView === 'table' ? 'active' : ''}`}
              onClick={() => navigate('/leads/table')}
            >
              Таблица
            </button>
            <button
              className={`view-toggle-button ${activeView === 'kanban' ? 'active' : ''}`}
              onClick={() => navigate('/leads/kanban')}
            >
              Канбан
            </button>
          </div>
          <button className="role-switch-button" onClick={logout}>
            Сменить роль ({getRoleLabel(session.role)})
          </button>
        </div>
      </div>

      <div className="leads-content">
        <div className="content-header">
          <div>
            <h2>Лиды {!permissions.can_read_all_leads && `(${getRoleLabel(session.role)})`}</h2>
            <p className="page-subtitle">
              Backend сам ограничивает доступ к данным и действиям.
            </p>
          </div>
          <div className="header-buttons">
            {permissions.can_create_leads && (
              <button
                className="primary-button"
                onClick={() => setLeadFormState({ open: true, mode: 'create', lead: null })}
              >
                + Добавить лид
              </button>
            )}
            {permissions.can_import_leads && (
              <button className="import-button" onClick={() => setIsImportOpen(true)}>
                Импорт CSV/XLSX
              </button>
            )}
          </div>
        </div>

        {permissions.can_read_all_leads && filterControls}
        {error && <p className="error-banner">{error}</p>}

        {isLoading ? (
          <div className="panel-card empty-panel">
            <p className="muted-copy">Загрузка лидов...</p>
          </div>
        ) : activeView === 'kanban' ? (
          <LeadsKanban
            leads={leads}
            session={session}
            onMoveStage={handleMoveStage}
            onOpenHistory={(leadUid) => void refreshHistory(leadUid)}
            onRequestReturn={handleRequestReturn}
            onDelete={handleDelete}
          />
        ) : (
          <LeadsTable
            leads={leads}
            session={session}
            onMoveStage={handleMoveStage}
            onOpenHistory={(leadUid) => void refreshHistory(leadUid)}
            onRequestReturn={handleRequestReturn}
            onEdit={(lead) => setLeadFormState({ open: true, mode: 'edit', lead })}
            onDelete={handleDelete}
          />
        )}
      </div>

      {leadFormState.open && (
        <LeadFormModal
          mode={leadFormState.mode}
          initialLead={leadFormState.lead}
          canManageOwner={isSalesHead}
          isSubmitting={isMutating}
          onClose={() => setLeadFormState({ open: false, mode: 'create', lead: null })}
          onSubmit={handleLeadSubmit}
        />
      )}

      {isImportOpen && (
        <ImportModal
          isSubmitting={isMutating}
          onClose={() => setIsImportOpen(false)}
          onSubmit={handleImportSubmit}
        />
      )}

      {historyState.open && (
        <LeadHistoryModal
          lead={historyState.lead}
          isLoading={historyState.isLoading}
          onClose={() => setHistoryState({ open: false, lead: null, isLoading: false })}
        />
      )}
    </div>
  );
}

export default LeadsPage;
