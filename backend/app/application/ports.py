from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.entities import AuditLogEntry, Lead, LeadComment, LeadStageEvent, StageReturnRequest
from app.domain.enums import AppRole, LeadStage, ReturnRequestStatus, SourcesCode, Users


class LeadRepository(Protocol):
    async def create(self, lead: Lead) -> Lead:
        ...

    async def get_by_id(self, lead_id: int) -> Lead | None:
        ...

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        ...

    async def delete_by_uid(self, lead_uid: str) -> None:
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

    async def update_details(
        self,
        lead_id: int,
        owner: Users,
        title: str | None,
        notes: str | None,
    ) -> Lead:
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


class ReturnRequestRepository(Protocol):
    async def create_return_request(self, request: StageReturnRequest) -> StageReturnRequest:
        ...

    async def get_return_request_by_id(self, request_id: int) -> StageReturnRequest | None:
        ...

    async def list_return_requests(
        self,
        *,
        status: ReturnRequestStatus | None,
        lead_id: int | None,
    ) -> list[StageReturnRequest]:
        ...

    async def list_return_requests_by_lead(self, lead_id: int) -> list[StageReturnRequest]:
        ...

    async def update_review(
        self,
        request_id: int,
        *,
        status: ReturnRequestStatus,
        reviewed_by: Users,
        review_comment: str,
        reviewed_at: datetime,
    ) -> StageReturnRequest:
        ...


class AuditLogRepository(Protocol):
    async def create_audit_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        ...

    async def list_audit_entries(
        self,
        *,
        lead_id: int | None,
        limit: int,
        offset: int,
    ) -> list[AuditLogEntry]:
        ...
