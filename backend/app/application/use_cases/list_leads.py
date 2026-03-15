from dataclasses import dataclass
from datetime import datetime

from app.application.ports import LeadRepository, StageEventRepository
from app.domain.entities import Lead
from app.domain.enums import LeadStage, SourcesCode, Users


@dataclass(slots=True)
class LeadStageInfo:
    entered_at: datetime
    left_at: datetime | None
    approved: bool


@dataclass(slots=True)
class LeadWithStageInfo:
    lead: Lead
    stage_info: dict[LeadStage, LeadStageInfo]


class ListLeadsUseCase:
    def __init__(self, lead_repository: LeadRepository, stage_repository: StageEventRepository):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository

    async def execute(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[LeadWithStageInfo]:
        leads = await self._lead_repository.list(
            owner=owner,
            stage=stage,
            source_code=source_code,
            limit=limit,
            offset=offset,
        )

        result: list[LeadWithStageInfo] = []
        for lead in leads:
            events = await self._stage_repository.list_by_lead(lead.id)
            stage_info: dict[LeadStage, LeadStageInfo] = {}
            for event in events:
                stage_info[event.stage] = LeadStageInfo(
                    entered_at=event.entered_at,
                    left_at=event.left_at,
                    approved=event.approved,
                )
            result.append(LeadWithStageInfo(lead=lead, stage_info=stage_info))

        return result
