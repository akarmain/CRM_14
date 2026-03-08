from datetime import UTC, datetime
from uuid import uuid4

from app.application.ports import LeadRepository, StageEventRepository
from app.domain.entities import Lead
from app.domain.enums import LeadStage, SourcesCode, Users


class CreateLeadUseCase:
    def __init__(self, lead_repository: LeadRepository, stage_repository: StageEventRepository):
        self._lead_repository = lead_repository
        self._stage_repository = stage_repository

    async def execute(
        self,
        source_code: SourcesCode,
        owner: Users,
        title: str | None,
        notes: str | None,
        lead_uid: str | None,
    ) -> Lead:
        now = datetime.now(UTC)
        new_lead = Lead(
            id=0,
            lead_uid=lead_uid or str(uuid4()),
            source_code=source_code,
            current_stage=LeadStage.new,
            owner=owner,
            title=title,
            notes=notes,
        )

        created = await self._lead_repository.create(new_lead)
        await self._stage_repository.create_stage_event(
            lead_id=created.id,
            stage=LeadStage.new,
            entered_at=now,
            approved=True,
        )
        return created
