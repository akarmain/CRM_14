from datetime import UTC, datetime
from secrets import choice
from string import ascii_letters, digits

from app.application.ports import LeadRepository, StageEventRepository
from app.core.errors import ConflictError
from app.domain.entities import Lead
from app.domain.enums import LeadStage, SourcesCode, Users

LEAD_UID_ALPHABET = ascii_letters + digits
LEAD_UID_LENGTH = 5
LEAD_UID_GENERATION_ATTEMPTS = 20


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
        attempts = 1 if lead_uid is not None else LEAD_UID_GENERATION_ATTEMPTS

        for _ in range(attempts):
            candidate_uid = lead_uid or self._generate_lead_uid()
            new_lead = Lead(
                id=0,
                lead_uid=candidate_uid,
                source_code=source_code,
                current_stage=LeadStage.new,
                owner=owner,
                title=title,
                notes=notes,
            )

            try:
                created = await self._lead_repository.create(new_lead)
                await self._stage_repository.create_stage_event(
                    lead_id=created.id,
                    stage=LeadStage.new,
                    entered_at=now,
                    approved=True,
                )
                return created
            except ConflictError:
                if lead_uid is not None:
                    raise

        raise ConflictError("Unable to generate a unique 5-character lead_uid.")

    def _generate_lead_uid(self) -> str:
        return "".join(choice(LEAD_UID_ALPHABET) for _ in range(LEAD_UID_LENGTH))
