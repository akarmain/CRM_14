from __future__ import annotations

import builtins
from datetime import datetime

from app.application.ports import (
    AuditLogRepository,
    CommentRepository,
    LeadRepository,
    ReturnRequestRepository,
    StageEventRepository,
)
from app.domain.entities import AuditLogEntry, Lead, LeadComment, LeadStageEvent, StageReturnRequest
from app.domain.enums import LeadStage, ReturnRequestStatus, SourcesCode, Users


class OneCRepositoryStub(
    LeadRepository,
    StageEventRepository,
    CommentRepository,
    ReturnRequestRepository,
    AuditLogRepository,
):
    _MSG = "STORAGE_MODE=1c is wired to a stub adapter. Implement real 1C integration first."

    async def create(self, lead: Lead) -> Lead:
        raise NotImplementedError(self._MSG)

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        raise NotImplementedError(self._MSG)

    async def get_by_id(self, lead_id: int) -> Lead | None:
        raise NotImplementedError(self._MSG)

    async def delete_by_uid(self, lead_uid: str) -> None:
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

    async def update_details(
        self,
        lead_id: int,
        owner: Users,
        title: str | None,
        notes: str | None,
    ) -> Lead:
        raise NotImplementedError(self._MSG)

    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
        approved: bool = True,
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

    async def create_return_request(self, request: StageReturnRequest) -> StageReturnRequest:
        raise NotImplementedError(self._MSG)

    async def get_return_request_by_id(self, request_id: int) -> StageReturnRequest | None:
        raise NotImplementedError(self._MSG)

    async def list_return_requests(
        self,
        *,
        status: ReturnRequestStatus | None,
        lead_id: int | None,
    ) -> list[StageReturnRequest]:
        raise NotImplementedError(self._MSG)

    async def list_return_requests_by_lead(self, lead_id: int) -> list[StageReturnRequest]:
        raise NotImplementedError(self._MSG)

    async def update_review(
        self,
        request_id: int,
        *,
        status: ReturnRequestStatus,
        reviewed_by: Users,
        review_comment: str,
        reviewed_at: datetime,
    ) -> StageReturnRequest:
        raise NotImplementedError(self._MSG)

    async def create_audit_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        raise NotImplementedError(self._MSG)

    async def list_audit_entries(
        self,
        *,
        lead_id: int | None,
        limit: int,
        offset: int,
    ) -> list[AuditLogEntry]:
        raise NotImplementedError(self._MSG)
