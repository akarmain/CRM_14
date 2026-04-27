from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import AuditLogRepository, CommentRepository, LeadRepository, ReturnRequestRepository, StageEventRepository
from app.core.errors import ConflictError, LeadNotFoundError
from app.domain.entities import AuditLogEntry, Lead, LeadComment, LeadStageEvent, StageReturnRequest
from app.domain.enums import AppRole, LeadStage, ReturnRequestStatus, SourcesCode, Users
from app.infrastructure.sql.models import (
    AuditLogModel,
    LeadCommentModel,
    LeadModel,
    LeadStageEventModel,
    StageReturnRequestModel,
)


class PostgresRepositories(
    LeadRepository,
    StageEventRepository,
    CommentRepository,
    ReturnRequestRepository,
    AuditLogRepository,
):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, lead: Lead) -> Lead:
        existing = await self.get_by_uid(lead.lead_uid)
        if existing is not None:
            raise ConflictError(f"lead_uid '{lead.lead_uid}' already exists.")

        model = LeadModel(
            lead_uid=lead.lead_uid,
            source_code=lead.source_code,
            current_stage=lead.current_stage,
            owner=lead.owner,
            title=lead.title,
            notes=lead.notes,
        )
        self._session.add(model)
        await self._session.flush()
        return _lead_entity(model)

    async def get_by_id(self, lead_id: int) -> Lead | None:
        model = await self._session.get(LeadModel, lead_id)
        return _lead_entity(model) if model is not None else None

    async def get_by_uid(self, lead_uid: str) -> Lead | None:
        result = await self._session.execute(
            select(LeadModel).where(LeadModel.lead_uid == lead_uid)
        )
        model = result.scalar_one_or_none()
        return _lead_entity(model) if model is not None else None

    async def delete_by_uid(self, lead_uid: str) -> None:
        await self._session.execute(delete(LeadModel).where(LeadModel.lead_uid == lead_uid))
        await self._session.flush()

    async def list(
        self,
        owner: Users | None,
        stage: LeadStage | None,
        source_code: SourcesCode | None,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        stmt = select(LeadModel).order_by(LeadModel.id).offset(offset).limit(limit)
        if owner is not None:
            stmt = stmt.where(LeadModel.owner == owner)
        if stage is not None:
            stmt = stmt.where(LeadModel.current_stage == stage)
        if source_code is not None:
            stmt = stmt.where(LeadModel.source_code == source_code)

        result = await self._session.execute(stmt)
        return [_lead_entity(model) for model in result.scalars().all()]

    async def update_stage(self, lead_id: int, new_stage: LeadStage) -> Lead:
        model = await self._session.get(LeadModel, lead_id)
        if model is None:
            raise LeadNotFoundError(f"Lead with id '{lead_id}' not found.")

        model.current_stage = new_stage
        await self._session.flush()
        return _lead_entity(model)

    async def update_details(
        self,
        lead_id: int,
        owner: Users,
        title: str | None,
        notes: str | None,
    ) -> Lead:
        model = await self._session.get(LeadModel, lead_id)
        if model is None:
            raise LeadNotFoundError(f"Lead with id '{lead_id}' not found.")

        model.owner = owner
        model.title = title
        model.notes = notes
        await self._session.flush()
        return _lead_entity(model)

    async def create_stage_event(
        self,
        lead_id: int,
        stage: LeadStage,
        entered_at: datetime,
        approved: bool = True,
    ) -> LeadStageEvent:
        duplicate = await self._session.execute(
            select(LeadStageEventModel).where(
                LeadStageEventModel.lead_id == lead_id,
                LeadStageEventModel.stage == stage,
                LeadStageEventModel.entered_at == entered_at,
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise ConflictError("Stage event uniqueness violated for (lead_id, stage, entered_at).")

        model = LeadStageEventModel(
            lead_id=lead_id,
            stage=stage,
            entered_at=entered_at,
            left_at=None,
            approved=approved,
        )
        self._session.add(model)
        await self._session.flush()
        return _stage_event_entity(model)

    async def close_open_event(self, lead_id: int, left_at: datetime) -> LeadStageEvent | None:
        result = await self._session.execute(
            select(LeadStageEventModel)
            .where(LeadStageEventModel.lead_id == lead_id, LeadStageEventModel.left_at.is_(None))
            .order_by(LeadStageEventModel.entered_at.desc(), LeadStageEventModel.id.desc())
        )
        model = result.scalars().first()
        if model is None:
            return None

        model.left_at = left_at
        await self._session.flush()
        return _stage_event_entity(model)

    async def list_by_lead(self, lead_id: int) -> list[LeadStageEvent]:
        result = await self._session.execute(
            select(LeadStageEventModel)
            .where(LeadStageEventModel.lead_id == lead_id)
            .order_by(LeadStageEventModel.entered_at.asc(), LeadStageEventModel.id.asc())
        )
        return [_stage_event_entity(model) for model in result.scalars().all()]

    async def create_comment(
        self,
        stage_event_id: int,
        author: Users,
        comment: str | None,
        created_at: datetime,
    ) -> LeadComment:
        existing = await self.get_by_stage_event_id(stage_event_id)
        if existing is not None:
            raise ConflictError(f"Comment already exists for stage_event_id '{stage_event_id}'.")

        model = LeadCommentModel(
            stage_event_id=stage_event_id,
            author=author,
            comment=comment,
            created_at=created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _comment_entity(model)

    async def get_by_stage_event_id(self, stage_event_id: int) -> LeadComment | None:
        result = await self._session.execute(
            select(LeadCommentModel).where(LeadCommentModel.stage_event_id == stage_event_id)
        )
        model = result.scalar_one_or_none()
        return _comment_entity(model) if model is not None else None

    async def create_return_request(self, request: StageReturnRequest) -> StageReturnRequest:
        model = StageReturnRequestModel(
            lead_id=request.lead_id,
            from_stage=request.from_stage,
            to_stage=request.to_stage,
            requested_by=request.requested_by,
            request_comment=request.request_comment,
            requested_at=request.requested_at,
            status=request.status,
            reviewed_by=request.reviewed_by,
            review_comment=request.review_comment,
            reviewed_at=request.reviewed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _return_request_entity(model)

    async def get_return_request_by_id(self, request_id: int) -> StageReturnRequest | None:
        model = await self._session.get(StageReturnRequestModel, request_id)
        return _return_request_entity(model) if model is not None else None

    async def list_return_requests(
        self,
        *,
        status: ReturnRequestStatus | None,
        lead_id: int | None,
    ) -> list[StageReturnRequest]:
        stmt = select(StageReturnRequestModel).order_by(
            StageReturnRequestModel.requested_at.desc(),
            StageReturnRequestModel.id.desc(),
        )
        if status is not None:
            stmt = stmt.where(StageReturnRequestModel.status == status)
        if lead_id is not None:
            stmt = stmt.where(StageReturnRequestModel.lead_id == lead_id)

        result = await self._session.execute(stmt)
        return [_return_request_entity(model) for model in result.scalars().all()]

    async def list_return_requests_by_lead(self, lead_id: int) -> list[StageReturnRequest]:
        return await self.list_return_requests(status=None, lead_id=lead_id)

    async def update_review(
        self,
        request_id: int,
        *,
        status: ReturnRequestStatus,
        reviewed_by: Users,
        review_comment: str,
        reviewed_at: datetime,
    ) -> StageReturnRequest:
        model = await self._session.get(StageReturnRequestModel, request_id)
        if model is None:
            raise LeadNotFoundError(f"Return request '{request_id}' not found.")

        model.status = status
        model.reviewed_by = reviewed_by
        model.review_comment = review_comment
        model.reviewed_at = reviewed_at
        await self._session.flush()
        return _return_request_entity(model)

    async def create_audit_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        model = AuditLogModel(
            lead_id=entry.lead_id,
            actor_role=entry.actor_role.value,
            action_type=entry.action_type,
            payload_json=entry.payload_json,
            created_at=entry.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _audit_entity(model)

    async def list_audit_entries(
        self,
        *,
        lead_id: int | None,
        limit: int,
        offset: int,
    ) -> list[AuditLogEntry]:
        stmt = (
            select(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc(), AuditLogModel.id.desc())
            .offset(offset)
            .limit(limit)
        )
        if lead_id is not None:
            stmt = stmt.where(AuditLogModel.lead_id == lead_id)

        result = await self._session.execute(stmt)
        return [_audit_entity(model) for model in result.scalars().all()]


def _lead_entity(model: LeadModel | None) -> Lead | None:
    if model is None:
        return None
    return Lead(
        id=model.id,
        lead_uid=model.lead_uid,
        source_code=model.source_code,
        current_stage=model.current_stage,
        owner=model.owner,
        title=model.title,
        notes=model.notes,
    )


def _stage_event_entity(model: LeadStageEventModel) -> LeadStageEvent:
    return LeadStageEvent(
        id=model.id,
        lead_id=model.lead_id,
        stage=model.stage,
        entered_at=model.entered_at,
        left_at=model.left_at,
        approved=model.approved,
    )


def _comment_entity(model: LeadCommentModel | None) -> LeadComment | None:
    if model is None:
        return None
    return LeadComment(
        id=model.id,
        stage_event_id=model.stage_event_id,
        author=model.author,
        comment=model.comment,
        created_at=model.created_at,
    )


def _return_request_entity(model: StageReturnRequestModel | None) -> StageReturnRequest | None:
    if model is None:
        return None
    return StageReturnRequest(
        id=model.id,
        lead_id=model.lead_id,
        from_stage=model.from_stage,
        to_stage=model.to_stage,
        requested_by=model.requested_by,
        request_comment=model.request_comment,
        requested_at=model.requested_at,
        status=model.status,
        reviewed_by=model.reviewed_by,
        review_comment=model.review_comment,
        reviewed_at=model.reviewed_at,
    )


def _audit_entity(model: AuditLogModel) -> AuditLogEntry:
    return AuditLogEntry(
        id=model.id,
        lead_id=model.lead_id,
        actor_role=AppRole(model.actor_role),
        action_type=model.action_type,
        payload_json=model.payload_json,
        created_at=model.created_at,
    )
