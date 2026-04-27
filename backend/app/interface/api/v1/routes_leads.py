from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import (
    AuditLogRepository,
    CommentRepository,
    LeadRepository,
    ReturnRequestRepository,
    StageEventRepository,
)
from app.application.use_cases.create_lead import CreateLeadUseCase
from app.application.use_cases.delete_lead import DeleteLeadUseCase
from app.application.use_cases.export_leads import ExportLeadsUseCase
from app.application.use_cases.list_stages import ListStagesUseCase
from app.application.use_cases.move_stage import MoveStageUseCase
from app.application.use_cases.update_lead import UpdateLeadUseCase
from app.core.auth import ensure_permission, get_current_role, is_manager_role, to_db_user
from app.core.deps import (
    get_audit_log_repository,
    get_comment_repository,
    get_create_lead_use_case,
    get_db_session,
    get_delete_lead_use_case,
    get_export_leads_use_case,
    get_lead_repository,
    get_list_stages_use_case,
    get_move_stage_use_case,
    get_return_request_repository,
    get_stage_event_repository,
    get_update_lead_use_case,
)
from app.core.errors import ForbiddenError, LeadNotFoundError
from app.core.sentinels import UNSET
from app.domain.enums import LeadStage, SourcesCode, Users
from app.domain.rules import ensure_forward_transition
from app.interface.api.schemas import (
    ImportLeadsResponse,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    MoveStageRequest,
    MoveStageResponse,
    NewLeadRequest,
    StageCommentResponse,
    StageEventResponse,
    LeadUpdateRequest,
)
from app.interface.api.v1.helpers import (
    build_lead_detail_response,
    build_lead_list_response,
    collect_leads,
    create_audit_entry,
    resolve_created_at,
    within_date_range,
)
from app.interface.api.v1.leads_export import render_leads_csv, render_leads_xlsx
from app.interface.api.v1.leads_import import LeadsImportError, parse_leads_import

router = APIRouter()


def _resolve_owner_for_create(role, payload: NewLeadRequest) -> Users:
    if is_manager_role(role):
        return to_db_user(role)
    if role.value == "sales_head":
        return payload.owner or Users.sales_head
    raise ForbiddenError("This role cannot create leads.")


def _ensure_visible_to_role(role, lead_owner: Users) -> None:
    if is_manager_role(role) and lead_owner != to_db_user(role):
        raise ForbiddenError("Managers can only access their own leads.")


async def _commit_if_needed(db_session: AsyncSession | None) -> None:
    if db_session is not None:
        await db_session.commit()


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    payload: NewLeadRequest,
    request: Request,
    use_case: CreateLeadUseCase = Depends(get_create_lead_use_case),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> LeadResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_create_leads")

    owner = _resolve_owner_for_create(role, payload)
    lead = await use_case.execute(
        source_code=payload.source_code,
        owner=owner,
        title=payload.title,
        notes=payload.notes,
        lead_uid=None,
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_created",
        lead_id=lead.id,
        payload_json={"lead_uid": lead.lead_uid, "owner": lead.owner.value},
    )
    await _commit_if_needed(db_session)
    return LeadResponse.model_validate(lead)


@router.post("/new-lead", response_model=LeadResponse, status_code=status.HTTP_200_OK)
async def create_legacy_new_lead(
    payload: NewLeadRequest,
    request: Request,
    use_case: CreateLeadUseCase = Depends(get_create_lead_use_case),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> LeadResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_create_leads")

    owner = _resolve_owner_for_create(role, payload)
    lead = await use_case.execute(
        source_code=payload.source_code,
        owner=owner,
        title=payload.title,
        notes=payload.notes,
        lead_uid=None,
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_created_legacy",
        lead_id=lead.id,
        payload_json={"lead_uid": lead.lead_uid, "owner": lead.owner.value},
    )
    await _commit_if_needed(db_session)
    return LeadResponse.model_validate(lead)


@router.post("/leads/import", response_model=ImportLeadsResponse, status_code=status.HTTP_201_CREATED)
async def import_leads(
    request: Request,
    file: UploadFile = File(...),
    use_case: CreateLeadUseCase = Depends(get_create_lead_use_case),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> ImportLeadsResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_import_leads")

    body = await file.read()
    default_owner = to_db_user(role) if is_manager_role(role) else None
    try:
        items = parse_leads_import(
            body,
            filename=file.filename,
            content_type=file.content_type,
            default_owner=default_owner,
        )
    except LeadsImportError as exc:
        raise HTTPException(status_code=422, detail=exc.as_detail()) from exc

    lead_uids: list[str] = []
    for item in items:
        created = await use_case.execute(
            source_code=item.source_code,
            owner=default_owner or item.owner,
            title=item.title,
            notes=item.notes,
            lead_uid=None,
        )
        lead_uids.append(created.lead_uid)

    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_imported",
        payload_json={"created": len(lead_uids), "filename": file.filename},
        lead_id=None,
    )
    await _commit_if_needed(db_session)
    return ImportLeadsResponse(created=len(lead_uids), lead_uids=lead_uids)


@router.get("/leads/export")
async def export_leads(
    request: Request,
    file_type: Literal["scv", "csv", "xlsx"] = Query(...),
    owner: Users | None = Query(default=None),
    use_case: ExportLeadsUseCase = Depends(get_export_leads_use_case),
) -> Response:
    role = get_current_role(request)
    ensure_permission(role, "can_export_leads")

    owner_filter = owner
    rows = await use_case.execute(owner=owner_filter)

    fmt = "csv" if file_type in ("scv", "csv") else "xlsx"
    if fmt == "csv":
        content = render_leads_csv(rows)
        media_type = "text/csv; charset=utf-8"
        ext = "csv"
    else:
        content = render_leads_xlsx(rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"leads_{stamp}.{ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/leads/{lead_uid}", response_model=LeadDetailResponse)
async def get_lead(
    lead_uid: str,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> LeadDetailResponse:
    role = get_current_role(request)
    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

    _ensure_visible_to_role(role, lead.owner)
    return await build_lead_detail_response(
        lead_uid,
        lead_repo=lead_repo,
        stage_repo=stage_repo,
        comment_repo=comment_repo,
        return_request_repo=return_request_repo,
        audit_repo=audit_repo,
    )


@router.delete("/leads/{lead_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_uid: str,
    request: Request,
    use_case: DeleteLeadUseCase = Depends(get_delete_lead_use_case),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> None:
    role = get_current_role(request)
    ensure_permission(role, "can_delete_leads")
    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

    await use_case.execute(lead_uid)
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_deleted",
        lead_id=lead.id,
        payload_json={"lead_uid": lead_uid},
    )
    await _commit_if_needed(db_session)


@router.patch("/leads/{lead_uid}", response_model=LeadResponse)
async def update_lead(
    lead_uid: str,
    payload: LeadUpdateRequest,
    request: Request,
    use_case: UpdateLeadUseCase = Depends(get_update_lead_use_case),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> LeadResponse:
    role = get_current_role(request)
    ensure_permission(role, "can_update_any_lead")

    updated = await use_case.execute(
        lead_uid,
        owner=payload.owner if "owner" in payload.model_fields_set else UNSET,
        title=payload.title if "title" in payload.model_fields_set else UNSET,
        notes=payload.notes if "notes" in payload.model_fields_set else UNSET,
    )
    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_updated",
        lead_id=updated.id,
        payload_json={"lead_uid": updated.lead_uid, "fields": sorted(payload.model_fields_set)},
    )
    await _commit_if_needed(db_session)
    return LeadResponse.model_validate(updated)


@router.get("/leads", response_model=list[LeadListResponse])
async def list_leads(
    request: Request,
    owner: Users | None = Query(default=None),
    stage: LeadStage | None = Query(default=None),
    source_code: SourcesCode | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    stage_repo: StageEventRepository = Depends(get_stage_event_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    return_request_repo: ReturnRequestRepository = Depends(get_return_request_repository),
) -> list[LeadListResponse]:
    role = get_current_role(request)

    owner_filter = owner
    if is_manager_role(role):
        owner_filter = to_db_user(role)

    leads = await collect_leads(
        lead_repo,
        owner=owner_filter,
        stage=stage,
        source_code=source_code,
    )
    items: list[LeadListResponse] = []
    for lead in leads:
        if is_manager_role(role) and lead.owner != to_db_user(role):
            continue
        item = await build_lead_list_response(
            lead,
            stage_repo=stage_repo,
            comment_repo=comment_repo,
            return_request_repo=return_request_repo,
        )
        if within_date_range(item.created_at, date_from=date_from, date_to=date_to):
            items.append(item)

    items.sort(key=lambda item: (item.created_at or datetime.min.replace(tzinfo=UTC), item.lead_uid))
    return items[offset : offset + limit]


@router.post("/leads/{lead_uid}/stage", response_model=MoveStageResponse)
async def move_stage(
    lead_uid: str,
    payload: MoveStageRequest,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    use_case: MoveStageUseCase = Depends(get_move_stage_use_case),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    db_session: AsyncSession | None = Depends(get_db_session),
) -> MoveStageResponse:
    role = get_current_role(request)
    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

    if is_manager_role(role):
        _ensure_visible_to_role(role, lead.owner)
        ensure_forward_transition(lead.current_stage, payload.stage)
        author = to_db_user(role)
    else:
        ensure_permission(role, "can_force_stage")
        author = to_db_user(role)

    result = await use_case.execute(
        lead_uid=lead_uid,
        stage=payload.stage,
        author=author,
        comment=payload.comment,
        allow_any_transition=not is_manager_role(role),
    )
    comment_payload = None
    if result.comment is not None:
        comment_payload = StageCommentResponse.model_validate(result.comment)

    await create_audit_entry(
        audit_repo,
        actor_role=role,
        action_type="lead_stage_changed",
        lead_id=result.lead.id,
        payload_json={
            "lead_uid": lead_uid,
            "from_stage": lead.current_stage.value,
            "to_stage": payload.stage.value,
        },
    )
    await _commit_if_needed(db_session)
    return MoveStageResponse(
        lead=LeadResponse.model_validate(result.lead),
        stage_event=StageEventResponse(
            id=result.stage_event.id,
            stage=result.stage_event.stage,
            entered_at=result.stage_event.entered_at,
            left_at=result.stage_event.left_at,
            approved=result.stage_event.approved,
            comment=comment_payload,
        ),
    )


@router.get("/leads/{lead_uid}/stage", response_model=list[StageEventResponse])
@router.get("/leads/{lead_uid}/stages", response_model=list[StageEventResponse])
async def list_stages(
    lead_uid: str,
    request: Request,
    lead_repo: LeadRepository = Depends(get_lead_repository),
    use_case: ListStagesUseCase = Depends(get_list_stages_use_case),
) -> list[StageEventResponse]:
    role = get_current_role(request)
    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")
    _ensure_visible_to_role(role, lead.owner)

    stages = await use_case.execute(lead_uid)
    payload = []
    for item in stages:
        comment_payload = None
        if item.comment is not None:
            comment_payload = StageCommentResponse.model_validate(item.comment)
        payload.append(
            StageEventResponse(
                id=item.stage_event.id,
                stage=item.stage_event.stage,
                entered_at=item.stage_event.entered_at,
                left_at=item.stage_event.left_at,
                approved=item.stage_event.approved,
                comment=comment_payload,
            )
        )
    return payload
