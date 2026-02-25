from dataclasses import dataclass

from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.core.errors import LeadNotFoundError
from app.domain.entities import LeadComment, LeadStageEvent


@dataclass(slots=True)
class StageWithComment:
    stage_event: LeadStageEvent
    comment: LeadComment | None


class ListStagesUseCase:
    def __init__(
        self,
        lead_repository: LeadRepository,
        stage_repository: StageEventRepository,
        comment_repository: CommentRepository,
    ):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository
        self._comment_repository = comment_repository

    async def execute(self, lead_uid: str) -> list[StageWithComment]:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

        events = await self._stage_repository.list_by_lead(lead.id)
        result: list[StageWithComment] = []
        for event in events:
            comment = await self._comment_repository.get_by_stage_event_id(event.id)
            result.append(StageWithComment(stage_event=event, comment=comment))

        return result
