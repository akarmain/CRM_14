from __future__ import annotations

from datetime import UTC, date, datetime, time

from app.application.ports import AuditLogRepository, CommentRepository, LeadRepository, ReturnRequestRepository, StageEventRepository
from app.core.errors import LeadNotFoundError
from app.domain.entities import AuditLogEntry, Lead, LeadComment, LeadStageEvent, StageReturnRequest
from app.domain.enums import AppRole, LeadStage, SourcesCode, Users
from app.interface.api.schemas import (
    AuditLogEntryResponse,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    LeadStageInfoItem,
    ReturnRequestResponse,
    StageInfoCommentResponse,
)


async def collect_leads(
    lead_repo: LeadRepository,
    *,
    owner: Users | None,
    stage: LeadStage | None,
    source_code: SourcesCode | None,
) -> list[Lead]:
    items: list[Lead] = []
    limit = 200
    offset = 0
    while True:
        batch = await lead_repo.list(
            owner=owner,
            stage=stage,
            source_code=source_code,
            limit=limit,
            offset=offset,
        )
        if not batch:
            break
        items.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return items


async def build_lead_list_response(
    lead: Lead,
    *,
    stage_repo: StageEventRepository,
    comment_repo: CommentRepository,
    return_request_repo: ReturnRequestRepository,
) -> LeadListResponse:
    stage_info = await build_stage_info(lead.id, stage_repo=stage_repo, comment_repo=comment_repo)
    requests = await return_request_repo.list_return_requests_by_lead(lead.id)
    lead_payload = LeadResponse.model_validate(lead).model_dump(exclude={"created_at"})
    return LeadListResponse(
        **lead_payload,
        created_at=resolve_created_at(stage_info),
        stage_info=stage_info,
        pending_return_requests=sum(1 for item in requests if item.status.value == "pending"),
    )


async def build_lead_detail_response(
    lead_uid: str,
    *,
    lead_repo: LeadRepository,
    stage_repo: StageEventRepository,
    comment_repo: CommentRepository,
    return_request_repo: ReturnRequestRepository,
    audit_repo: AuditLogRepository,
) -> LeadDetailResponse:
    lead = await lead_repo.get_by_uid(lead_uid)
    if lead is None:
        raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")

    list_item = await build_lead_list_response(
        lead,
        stage_repo=stage_repo,
        comment_repo=comment_repo,
        return_request_repo=return_request_repo,
    )
    return_requests = await return_request_repo.list_return_requests_by_lead(lead.id)
    audit_entries = await audit_repo.list_audit_entries(lead_id=lead.id, limit=50, offset=0)
    return LeadDetailResponse(
        **list_item.model_dump(),
        return_requests=[
            serialize_return_request(item, lead_uid=lead.lead_uid) for item in return_requests
        ],
        audit_entries=[AuditLogEntryResponse.model_validate(item) for item in audit_entries],
    )


async def build_stage_info(
    lead_id: int,
    *,
    stage_repo: StageEventRepository,
    comment_repo: CommentRepository,
) -> list[LeadStageInfoItem]:
    events = await stage_repo.list_by_lead(lead_id)
    output: list[LeadStageInfoItem] = []
    for event in events:
        comment = await comment_repo.get_by_stage_event_id(event.id)
        comments = []
        if comment is not None:
            comments = [
                StageInfoCommentResponse(author=comment.author, comment=comment.comment)
            ]
        output.append(
            LeadStageInfoItem(
                stage=event.stage,
                entered_at=event.entered_at,
                left_at=event.left_at,
                approved=event.approved,
                comment=comments,
            )
        )
    output.sort(key=lambda item: (item.entered_at, item.stage.value))
    return output


def resolve_created_at(stage_info: list[LeadStageInfoItem]) -> datetime | None:
    new_stage_entries = [item.entered_at for item in stage_info if item.stage == LeadStage.new]
    if not new_stage_entries:
        return None
    return min(new_stage_entries)


def within_date_range(created_at: datetime | None, *, date_from: date | None, date_to: date | None) -> bool:
    if created_at is None:
        return date_from is None and date_to is None
    if date_from is not None and created_at < datetime.combine(date_from, time.min, tzinfo=UTC):
        return False
    if date_to is not None and created_at > datetime.combine(date_to, time.max, tzinfo=UTC):
        return False
    return True


async def create_audit_entry(
    audit_repo: AuditLogRepository,
    *,
    actor_role: AppRole,
    action_type: str,
    payload_json: dict,
    lead_id: int | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        id=0,
        lead_id=lead_id,
        actor_role=actor_role,
        action_type=action_type,
        payload_json=payload_json,
        created_at=datetime.now(UTC),
    )
    return await audit_repo.create_audit_entry(entry)


def serialize_return_request(request: StageReturnRequest, *, lead_uid: str | None) -> ReturnRequestResponse:
    return ReturnRequestResponse(
        id=request.id,
        lead_id=request.lead_id,
        lead_uid=lead_uid,
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
