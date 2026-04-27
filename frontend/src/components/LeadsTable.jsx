import React, { useMemo, useState } from 'react';
import { getForwardTargets, getRoleLabel, getSourceLabel, getStageLabel, STAGE_OPTIONS } from '../lib/leadsApi';

function LeadsTable({
  leads,
  session,
  onOpenHistory,
  onMoveStage,
  onRequestReturn,
  onEdit,
  onDelete,
}) {
  const [stageSelection, setStageSelection] = useState({});
  const isSalesHead = session.role === 'sales_head';
  const isManager = session.role === 'manager_1' || session.role === 'manager_2';
  const canReadAll = session.permissions.can_read_all_leads;

  const rows = useMemo(() => leads, [leads]);

  return (
    <div className="table-container">
      <table className="leads-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Описание</th>
            <th>Источник</th>
            <th>Стадия</th>
            {canReadAll && <th>Менеджер</th>}
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={canReadAll ? 7 : 6} className="empty-cell">
                {isManager ? 'У вас нет лидов' : 'Нет данных для отображения'}
              </td>
            </tr>
          ) : (
            rows.map((lead) => {
              const allowedForwardTargets = getForwardTargets(lead.current_stage);
              const selectedStage = stageSelection[lead.lead_uid] ?? lead.current_stage;

              return (
                <tr key={lead.lead_uid}>
                  <td>{lead.lead_uid}</td>
                  <td><strong>{lead.title || 'Без названия'}</strong></td>
                  <td>{lead.notes ? <p className="cell-note">{lead.notes}</p> : 'Без описания'}</td>
                  <td>{getSourceLabel(lead.source_code)}</td>
                  <td>
                    <span className="status-text">{getStageLabel(lead.current_stage)}</span>
                  </td>
                  {canReadAll && <td>{getRoleLabel(lead.owner)}</td>}
                  <td>
                    <div className="action-stack">
                      <button className="secondary-button" onClick={() => onOpenHistory(lead.lead_uid)}>
                        История
                      </button>
                      {isManager && (
                        <>
                          <div className="inline-actions">
                            {allowedForwardTargets.map((target) => (
                              <button
                                key={target}
                                className="chip-button"
                                onClick={() => onMoveStage(lead, target)}
                              >
                                {getStageLabel(target)}
                              </button>
                            ))}
                          </div>
                          {lead.current_stage !== 'new' && lead.pending_return_requests === 0 && (
                            <button className="ghost-button" onClick={() => onRequestReturn(lead)}>
                              Запросить возврат
                            </button>
                          )}
                        </>
                      )}
                      {isSalesHead && (
                        <>
                          <div className="inline-actions">
                            <select
                              value={selectedStage}
                              onChange={(event) =>
                                setStageSelection((current) => ({
                                  ...current,
                                  [lead.lead_uid]: event.target.value,
                                }))
                              }
                            >
                              {STAGE_OPTIONS.map((stage) => (
                                <option key={stage.value} value={stage.value}>
                                  {stage.label}
                                </option>
                              ))}
                            </select>
                            <button className="chip-button" onClick={() => onMoveStage(lead, selectedStage)}>
                              Применить
                            </button>
                          </div>
                          <div className="inline-actions">
                            <button className="ghost-button" onClick={() => onEdit(lead)}>
                              Редактировать
                            </button>
                            <button className="danger-button" onClick={() => onDelete(lead)}>
                              Удалить
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export default LeadsTable;
