from __future__ import annotations

import builtins
from datetime import datetime

from app.application.ports import CommentRepository, LeadRepository, StageEventRepository
from app.domain.entities import Lead, LeadComment, LeadStageEvent
from app.domain.enums import LeadStage, SourcesCode, Users


class OneCRepositoryStub(LeadRepository, StageEventRepository, CommentRepository):
    _MSG = "STORAGE_MODE=1c is wired to a stub adapter. Implement real 1C integration first."

    async def create(self, lead: Lead) -> Lead:
        raise NotImplementedError(self._MSG)

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        raise NotImplementedError(self._MSG)

    async def list(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        raise NotImplementedError(self._MSG)

    async def update_stage(self, lead_id: int, new_stage: LeadStage) -> Lead:
        raise NotImplementedError(self._MSG)

    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
    ) -> LeadStageEvent:
        raise NotImplementedError(self._MSG)

    async def close_open_event(self, lead_id: int, left_at: datetime) -> LeadStageEvent | None:
        raise NotImplementedError(self._MSG)

    async def list_by_lead(self, lead_id: int) -> builtins.list[LeadStageEvent]:
        raise NotImplementedError(self._MSG)

    async def create_comment(
        self,
        stage_event_id: int,
        author: Users,
        comment: str | None,
        created_at: datetime,
    ) -> LeadComment:
        raise NotImplementedError(self._MSG)

    async def get_by_stage_event_id(self, stage_event_id: int) -> LeadComment | None:
        raise NotImplementedError(self._MSG)
