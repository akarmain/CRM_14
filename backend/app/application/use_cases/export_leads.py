from __future__ import annotations

from dataclasses import dataclass

from app.application.dtos import LeadExportRow
from app.application.ports import LeadRepository, StageEventRepository
from app.domain.entities import LeadStageEvent
from app.domain.enums import LeadStage, Users


@dataclass(slots=True)
class LeadExportData:
    rows: list[LeadExportRow]
    stage_events_by_lead_uid: dict[str, list[LeadStageEvent]]


class ExportLeadsUseCase:
    def __init__(self, lead_repository: LeadRepository, stage_repository: StageEventRepository):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository

    async def execute(self, *, owner: Users | None) -> list[LeadExportRow]:
        result = await self.execute_with_stage_events(owner=owner)
        return result.rows

    async def execute_with_stage_events(self, *, owner: Users | None) -> LeadExportData:
        rows: list[LeadExportRow] = []
        stage_events_by_lead_uid: dict[str, list[LeadStageEvent]] = {}

        limit = 200
        offset = 0
        while True:
            leads = await self._lead_repository.list(
                owner=owner,
                stage=None,
                source_code=None,
                limit=limit,
                offset=offset,
            )
            if not leads:
                break

            for lead in leads:
                events = await self._stage_repository.list_by_lead(lead.id)
                stage_events_by_lead_uid[lead.lead_uid] = events
                entered_at = _resolve_entered_at(
                    events=events,
                    current_stage=lead.current_stage,
                )
                rows.append(
                    LeadExportRow(
                        lead_uid=lead.lead_uid,
                        title=lead.title,
                        notes=lead.notes,
                        owner=lead.owner,
                        stage=lead.current_stage,
                        entered_at=entered_at,
                        source_code=lead.source_code,
                    )
                )

            if len(leads) < limit:
                break
            offset += limit

        return LeadExportData(
            rows=rows,
            stage_events_by_lead_uid=stage_events_by_lead_uid,
        )


def _resolve_entered_at(*, events: list[LeadStageEvent], current_stage: LeadStage):
    open_events = [e for e in events if getattr(e, "left_at", None) is None]
    if open_events:
        open_events.sort(key=lambda e: (e.entered_at, e.id))
        open_event = open_events[-1]
        if open_event.stage == current_stage:
            return open_event.entered_at

    candidates = [e for e in events if e.stage == current_stage]
    if not candidates:
        return None
    candidates.sort(key=lambda e: (e.entered_at, e.id))
    return candidates[-1].entered_at
