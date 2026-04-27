from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import AuditLogRepository, LeadRepository, ReturnRequestRepository
from app.application.use_cases.move_stage import MoveStageUseCase
from app.core.auth import ensure_permission, get_current_role, is_manager_role, to_db_user
from app.core.deps import (
    get_audit_log_repository,
    get_db_session,
    get_lead_repository,
    get_move_stage_use_case,
    get_return_request_repository,
)
from app.core.errors import ConflictError, ForbiddenError, LeadNotFoundError
from app.domain.entities import StageReturnRequest
from app.domain.enums import ReturnRequestStatus
from app.domain.rules import resolve_previous_stage
from app.interface.api.schemas import CreateReturnRequest, ReturnRequestResponse, ReviewReturnRequest
from app.interface.api.v1.helpers import create_audit_entry, serialize_return_request

router = APIRouter()


@router.post("/leads/{lead_uid}/return-requests", response_model=ReturnRequestResponse)
async def create_return_request(
    lead_uid: str,
    payload: CreateReturnRequest,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ReturnRequestResponse:
    role = get_current_role(request)
    if not is_manager_role(role):
        raise ForbiddenError("Only managers can request a return to a previous stage.")

    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

    actor = to_db_user(role)
    if lead.owner != actor:
        raise ForbiddenError("Managers can only request returns for their own leads.")

    target_stage = resolve_previous_stage(lead.current_stage)
    pending_requests = await return_request_repo.list_return_requests(
        status=ReturnRequestStatus.pending,
        lead_id=lead.id,
    )
    if pending_requests:
        raise ConflictError("There is already a pending return request for this lead.")

    created = await return_request_repo.create_return_request(
        StageReturnRequest(
            id=0,
            lead_id=lead.id,
            from_stage=lead.current_stage,
            to_stage=target_stage,
            requested_by=actor,
            request_comment=payload.comment,
            requested_at=datetime.now(UTC),
            status=ReturnRequestStatus.pending,
            reviewed_by=None,
            review_comment=None,
            reviewed_at=None,
        )
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="return_request_created",
        lead_id=lead.id,
        payload_json={
            "lead_uid": lead.lead_uid,
            "from_stage": lead.current_stage.value,
            "to_stage": target_stage.value,
        },
    )
    if db_session is not None:
        await db_session.commit()
    return serialize_return_request(created, lead_uid=lead.lead_uid)


@router.get("/return-requests", response_model=list[ReturnRequestResponse])
async def list_return_requests(
    request: Request,
    status: ReturnRequestStatus | None = Query(default=ReturnRequestStatus.pending),
    lead_uid: str | None = Query(default=None),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
) -> list[ReturnRequestResponse]:
    role = get_current_role(request)
    ensure_permission(role, "can_review_returns")

    lead_id: int | None = None
    if lead_uid is not None:
        lead = await lead_repo.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")
        lead_id = lead.id

    items = await return_request_repo.list_return_requests(status=status, lead_id=lead_id)
    lead_uid_map: dict[int, str | None] = {}
    if lead_id is not None and lead_uid is not None:
        lead_uid_map[lead_id] = lead_uid
    else:
        for item in items:
            if item.lead_id in lead_uid_map:
                continue
            lead = await lead_repo.get_by_id(item.lead_id)
            lead_uid_map[item.lead_id] = lead.lead_uid if lead is not None else None
    return [serialize_return_request(item, lead_uid=lead_uid_map.get(item.lead_id)) for item in items]


@router.post("/return-requests/{request_id}/approve", response_model=ReturnRequestResponse)
async def approve_return_request(
    request_id: int,
    payload: ReviewReturnRequest,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    move_stage_use_case: MoveStageUseCase = Depends(get_move_stage_use_case),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ReturnRequestResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_review_returns")

    return_request = await return_request_repo.get_return_request_by_id(request_id)
    if return_request is None:
        raise LeadNotFoundError(f"Return request '{request_id}' not found.")
    if return_request.status != ReturnRequestStatus.pending:
        raise ConflictError("Return request has already been reviewed.")

    lead = await lead_repo.get_by_id(return_request.lead_id)
    if lead is None:
        raise LeadNotFoundError(f"Lead with id '{return_request.lead_id}' not found.")
    if lead.current_stage != return_request.from_stage:
        raise ConflictError("Lead stage has changed since the return request was created.")

    reviewer = to_db_user(role)
    await move_stage_use_case.execute(
        lead_uid=lead.lead_uid,
        stage=return_request.to_stage,
        author=reviewer,
        comment=payload.review_comment,
        allow_any_transition=True,
    )
    updated = await return_request_repo.update_review(
        request_id,
        status=ReturnRequestStatus.approved,
        reviewed_by=reviewer,
        review_comment=payload.review_comment,
        reviewed_at=datetime.now(UTC),
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="return_request_approved",
        lead_id=lead.id,
        payload_json={
            "request_id": request_id,
            "lead_uid": lead.lead_uid,
            "to_stage": return_request.to_stage.value,
        },
    )
    if db_session is not None:
        await db_session.commit()
    return serialize_return_request(updated, lead_uid=lead.lead_uid)


@router.post("/return-requests/{request_id}/reject", response_model=ReturnRequestResponse)
async def reject_return_request(
    request_id: int,
    payload: ReviewReturnRequest,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ReturnRequestResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_review_returns")

    return_request = await return_request_repo.get_return_request_by_id(request_id)
    if return_request is None:
        raise LeadNotFoundError(f"Return request '{request_id}' not found.")
    if return_request.status != ReturnRequestStatus.pending:
        raise ConflictError("Return request has already been reviewed.")

    lead = await lead_repo.get_by_id(return_request.lead_id)
    if lead is None:
        raise LeadNotFoundError(f"Lead with id '{return_request.lead_id}' not found.")

    reviewer = to_db_user(role)
    updated = await return_request_repo.update_review(
        request_id,
        status=ReturnRequestStatus.rejected,
        reviewed_by=reviewer,
        review_comment=payload.review_comment,
        reviewed_at=datetime.now(UTC),
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="return_request_rejected",
        lead_id=lead.id,
        payload_json={"request_id": request_id, "lead_uid": lead.lead_uid},
    )
    if db_session is not None:
        await db_session.commit()
    return serialize_return_request(updated, lead_uid=lead.lead_uid)
