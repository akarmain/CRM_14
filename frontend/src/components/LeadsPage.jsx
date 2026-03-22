import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import LeadsTable from './LeadsTable';
import LeadsKanban from './LeadsKanban';
import AddLeadModal from './AddLeadModal';
import ImportModal from './ImportModal';
import '../App.css';

function LeadsPage({
  role,
  onLogout,
  leads,
  isLoading,
  error,
  onLeadCreate,
  onLeadsImport,
  onLeadDelete,
  onLeadsClear,
  onLeadStatusChange,
}) {
  const navigate = useNavigate();
  const { viewMode: urlViewMode } = useParams();
  const viewMode = urlViewMode || 'table';
  const [showChoiceModal, setShowChoiceModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showManualModal, setShowManualModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAnalyst = role === 'Аналитик';
  const hasAdvancedAccess = role === 'Аналитик' || role === 'Руководитель отдела продаж';
  const isManager = role === 'Менеджер 1' || role === 'Менеджер 2';

  const handleRoleSwitch = () => {
    onLogout();
    navigate('/');
  };

  const handleAddLead = () => {
    setShowChoiceModal(true);
  };

  const handleManualAdd = () => {
    setShowChoiceModal(false);
    setShowManualModal(true);
  };

  const handleImportAdd = () => {
    setShowChoiceModal(false);
    setShowImportModal(true);
  };

  const handleManualSubmit = async (newLead) => {
    setIsSubmitting(true);
    try {
      await onLeadCreate(newLead);
      setShowManualModal(false);
      alert('Лид успешно добавлен');
    } catch (submitError) {
      alert(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleImportSubmit = async (importedLeads) => {
    setIsSubmitting(true);
    try {
      const createdLeads = await onLeadsImport(importedLeads);
      setShowImportModal(false);
      alert(`Импортировано ${createdLeads.length} записей`);
    } catch (submitError) {
      alert(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteLead = async (leadUid) => {
    if (window.confirm('Удалить эту запись?')) {
      setIsSubmitting(true);
      try {
        await onLeadDelete(leadUid);
      } catch (submitError) {
        alert(submitError.message);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить все свои данные?')) return;

    const leadsToDelete = isManager ? filteredLeads : leads;

    if (leadsToDelete.length === 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onLeadsClear(leadsToDelete);
    } catch (submitError) {
      alert(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (leadUid, newStatus) => {
    if (isAnalyst) return;

    setIsSubmitting(true);
    try {
      await onLeadStatusChange(leadUid, newStatus);
    } catch (submitError) {
      alert(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredLeads = hasAdvancedAccess ? leads : leads.filter(l => l.manager === role);

  const handleViewModeChange = (mode) => {
    navigate(`/leads/${mode}`);
  };

  return (
    <div className="leads-page">
      <div className="top-bar">
        <div className="top-bar-left">
          {hasAdvancedAccess && (
            <>
              <button className="top-bar-button">Отчеты</button>
              <button className="top-bar-button">Экспорт</button>
              <button className="top-bar-button">Запросы</button>
            </>
          )}
        </div>
        <div className="top-bar-right">
          <div className="view-toggle">
            <button 
              className={`view-toggle-button ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => handleViewModeChange('table')}
            >
              Таблица
            </button>
            <button 
              className={`view-toggle-button ${viewMode === 'kanban' ? 'active' : ''}`}
              onClick={() => handleViewModeChange('kanban')}
            >
              Канбан
            </button>
          </div>
          <button className="role-switch-button" onClick={handleRoleSwitch}>
            Сменить роль ({role})
          </button>
        </div>
      </div>

      <div className="leads-content">
        <div className="content-header">
          <h2>Лиды {!hasAdvancedAccess && `(${role})`}</h2>
          <div className="header-buttons">
            {isManager && (
              <>
                <button className="import-button" onClick={handleAddLead}>
                  + Добавить лид
                </button>
                {filteredLeads.length > 0 && (
                  <button className="clear-button" onClick={handleClearAll}>
                    Очистить мои лиды
                  </button>
                )}
              </>
            )}
            {hasAdvancedAccess && leads.length > 0 && (
              <button className="clear-button" onClick={handleClearAll}>
                Очистить все лиды
              </button>
            )}
          </div>
        </div>

        {error && <p className="empty-table">{error}</p>}

        {isLoading ? (
          <p className="empty-table">Загрузка лидов из FastAPI...</p>
        ) : (
          <>
            {viewMode === 'table' ? (
              <LeadsTable 
                leads={filteredLeads}
                isBoss={hasAdvancedAccess}
                isManager={isManager}
                onDelete={handleDeleteLead}
              />
            ) : (
              <LeadsKanban 
                leads={filteredLeads}
                isBoss={hasAdvancedAccess}
                isAnalyst={isAnalyst}
                onDelete={handleDeleteLead}
                onStatusChange={handleStatusChange}
              />
            )}
          </>
        )}

      </div>

      {/* Модальное окно выбора способа добавления */}
      {showChoiceModal && (
        <div className="modal-overlay" onClick={() => setShowChoiceModal(false)}>
          <div className="modal-content choice-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Выберите способ добавления</h3>
            
            <div className="choice-buttons">
              <button className="choice-button" onClick={handleManualAdd}>
                <span className="choice-text">Добавить вручную</span>
                <span className="choice-description">Заполнить форму с данными лида</span>
              </button>
              
              <button className="choice-button" onClick={handleImportAdd}>
                <span className="choice-text">Импорт через CSV</span>
                <span className="choice-description">Загрузить несколько лидов сразу</span>
              </button>
            </div>

            <button className="modal-button cancel" onClick={() => setShowChoiceModal(false)}>
              Отмена
            </button>
          </div>
        </div>
      )}

      {/* Модальное окно для ручного добавления */}
      {showManualModal && (
        <AddLeadModal 
          role={role}
          isSubmitting={isSubmitting}
          onClose={() => setShowManualModal(false)}
          onAdd={handleManualSubmit}
        />
      )}

      {/* Модальное окно для импорта через CSV */}
      {showImportModal && (
        <ImportModal 
          role={role}
          isSubmitting={isSubmitting}
          onClose={() => setShowImportModal(false)}
          onImport={handleImportSubmit}
        />
      )}
    </div>
  );
}

export default LeadsPage;
