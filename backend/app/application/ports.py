from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.entities import Lead, LeadComment, LeadStageEvent
from app.domain.enums import LeadStage, SourcesCode, Users


class LeadRepository(Protocol):
    async def create(self, lead: Lead) -> Lead:
        ...

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        ...

    async def list(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        ...

    async def update_stage(self, lead_id: int, new_stage: LeadStage) -> Lead:
        ...


class StageEventRepository(Protocol):
    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
        approved: bool = True,
    ) -> LeadStageEvent:
        ...

    async def close_open_event(self, lead_id: int, left_at: datetime) -> LeadStageEvent | None:
        ...

    async def list_by_lead(self, lead_id: int) -> list[LeadStageEvent]:
        ...


class CommentRepository(Protocol):
    async def create_comment(
        self,
        stage_event_id: int,
        author: Users,
        comment: str | None,
        created_at: datetime,
    ) -> LeadComment:
        ...

    async def get_by_stage_event_id(self, stage_event_id: int) -> LeadComment | None:
        ...
