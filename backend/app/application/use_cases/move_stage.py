from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.core.errors import ConflictError, LeadNotFoundError
from app.domain.entities import Lead, LeadComment, LeadStageEvent
from app.domain.enums import LeadStage, Users
from app.domain.rules import ensure_transition_allowed


@dataclass(slots=True)
class MoveStageResult:
    lead: Lead
    stage_event: LeadStageEvent
    comment: LeadComment | None


class MoveStageUseCase:
    def __init__(
        self,
        lead_repository: LeadRepository,
        stage_repository: StageEventRepository,
        comment_repository: CommentRepository,
    ):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository
        self._comment_repository = comment_repository

    async def execute(
        self,
        lead_uid: str,
        stage: LeadStage,
        author: Users,
        comment: str | None,
    ) -> MoveStageResult:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

        ensure_transition_allowed(lead.current_stage, stage)

        now = datetime.now(UTC)
        closed_event = await self._stage_repository.close_open_event(lead.id, left_at=now)
        if closed_event is None:
            raise ConflictError("No open stage event found for lead.")

        new_event = await self._stage_repository.create_stage_event(
            lead_id=lead.id,
            stage=stage,
            entered_at=now,
            approved=True,
        )
        updated_lead = await self._lead_repository.update_stage(lead.id, new_stage=stage)

        created_comment: LeadComment | None = None
        if comment is not None:
            created_comment = await self._comment_repository.create_comment(
                stage_event_id=new_event.id,
                author=author,
                comment=comment,
                created_at=now,
            )

        return MoveStageResult(lead=updated_lead, stage_event=new_event, comment=created_comment)
