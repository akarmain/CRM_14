from app.application.ports import LeadRepository
from app.core.errors import LeadNotFoundError


class DeleteLeadUseCase:
    def __init__(self, lead_repository: LeadRepository):
        self._lead_repository = lead_repository

    async def execute(self, lead_uid: str) -> None:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

        await self._lead_repository.delete_by_uid(lead_uid)

