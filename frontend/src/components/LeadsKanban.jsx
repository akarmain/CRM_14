import React from 'react';
import { getForwardTargets, getRoleLabel, getSourceLabel, getStageLabel, STAGE_OPTIONS } from '../lib/leadsApi';

function LeadsKanban({
  leads,
  session,
  onMoveStage,
  onOpenHistory,
  onRequestReturn,
  onDelete,
}) {
  const isAnalyst = session.role === 'analyst';
  const isManager = session.role === 'manager_1' || session.role === 'manager_2';
  const isSalesHead = session.role === 'sales_head';

  const columns = STAGE_OPTIONS.map((stage) => ({
    ...stage,
    leads: leads.filter((lead) => lead.current_stage === stage.value),
  }));

  const canMoveTo = (lead, targetStage) => {
    if (isAnalyst) {
      return false;
    }
    if (isSalesHead) {
      return lead.current_stage !== targetStage;
    }
    return getForwardTargets(lead.current_stage).includes(targetStage);
  };

  const handleDrop = (event, targetStage) => {
    event.preventDefault();
    const rawLead = event.dataTransfer.getData('application/crm-lead');
    if (!rawLead) {
      return;
    }
    const lead = JSON.parse(rawLead);
    if (!canMoveTo(lead, targetStage)) {
      return;
    }
    onMoveStage(lead, targetStage);
  };

  return (
    <div className="kanban-container">
      {columns.map((column) => (
        <section
          key={column.value}
          className="kanban-column"
          onDragOver={(event) => !isAnalyst && event.preventDefault()}
          onDrop={(event) => handleDrop(event, column.value)}
        >
          <div className="kanban-column-header">
            <h3>{column.label}</h3>
            <span>{column.leads.length}</span>
          </div>
          <div className="kanban-column-body">
            {column.leads.length === 0 ? (
              <div className="kanban-empty">Нет лидов</div>
            ) : (
              column.leads.map((lead) => (
                <article
                  key={lead.lead_uid}
                  className="kanban-card"
                  draggable={!isAnalyst}
                  onDragStart={(event) => {
                    if (isAnalyst) {
                      return;
                    }
                    event.dataTransfer.setData('application/crm-lead', JSON.stringify(lead));
                  }}
                >
                  <div className="kanban-card-header">
                    <span className="kanban-card-id">ID: {lead.lead_uid}</span>
                    <span className="kanban-card-manager">{getRoleLabel(lead.owner)}</span>
                  </div>
                  <h4>{lead.title || 'Без названия'}</h4>
                  {lead.notes && <p className="kanban-card-notes">{lead.notes}</p>}
                  {!lead.notes && <p className="kanban-card-notes muted-copy">Без описания</p>}
                  <div className="kanban-card-actions">
                    <button className="ghost-button" onClick={() => onOpenHistory(lead.lead_uid)}>
                      История
                    </button>
                    {isManager && lead.current_stage !== 'new' && lead.pending_return_requests === 0 && (
                      <button className="ghost-button" onClick={() => onRequestReturn(lead)}>
                        Возврат
                      </button>
                    )}
                  </div>
                  <div className="kanban-card-footer">
                    <span className="kanban-card-source">{getSourceLabel(lead.source_code)}</span>
                    {isSalesHead && (
                      <button className="delete-button-small" onClick={() => onDelete(lead)}>
                        ✕
                      </button>
                    )}
                  </div>
                  {!isAnalyst && (
                    <div className="kanban-drop-hint">
                      Доступные переходы: {isSalesHead
                        ? STAGE_OPTIONS.filter((stage) => stage.value !== lead.current_stage)
                            .map((stage) => getStageLabel(stage.value))
                            .join(', ')
                        : getForwardTargets(lead.current_stage).map((stage) => getStageLabel(stage)).join(', ') || 'нет'}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </section>
      ))}
    </div>
  );
}

export default LeadsKanban;
