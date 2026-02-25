from app.application.ports import LeadRepository
from app.core.errors import LeadNotFoundError
from app.domain.entities import Lead


class GetLeadUseCase:
    def __init__(self, lead_repository: LeadRepository):
        self._lead_repository = lead_repository

    async def execute(self, lead_uid: str) -> Lead:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")
        return lead
