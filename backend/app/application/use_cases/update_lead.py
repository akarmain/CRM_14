from __future__ import annotations

from app.application.ports import LeadRepository
from app.core.errors import AppError, LeadNotFoundError
from app.core.sentinels import UNSET, _Unset
from app.domain.entities import Lead
from app.domain.enums import Users


class UpdateLeadUseCase:
    def __init__(self, lead_repository: LeadRepository):
        self._lead_repository = lead_repository

    async def execute(
        self,
        lead_uid: str,
        *,
        owner: Users | _Unset = UNSET,
        title: str | None | _Unset = UNSET,
        notes: str | None | _Unset = UNSET,
    ) -> Lead:
        lead = await self._lead_repository.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

        if owner is UNSET:
            new_owner = lead.owner
        else:
            if owner is None:
                raise AppError("owner cannot be null")
            new_owner = owner

        new_title = lead.title if title is UNSET else title
        new_notes = lead.notes if notes is UNSET else notes

        return await self._lead_repository.update_details(
            lead_id=lead.id,
            owner=new_owner,
            title=new_title,
            notes=new_notes,
        )
