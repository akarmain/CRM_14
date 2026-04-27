from fastapi import APIRouter, Depends, Query, Request

from app.application.ports import AuditLogRepository, LeadRepository
from app.core.auth import ensure_permission, get_current_role
from app.core.deps import get_audit_log_repository, get_lead_repository
from app.core.errors import LeadNotFoundError
from app.interface.api.schemas import AuditLogEntryResponse

router = APIRouter()


@router.get("/audit-log", response_model=list[AuditLogEntryResponse])
async def list_audit_log(
    request: Request,
    lead_uid: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> list[AuditLogEntryResponse]:
    role = get_current_role(request)
    ensure_permission(role, "can_view_audit_log")

    lead_id: int | None = None
    if lead_uid is not None:
        lead = await lead_repo.get_by_uid(lead_uid)
        if lead is None:
            raise LeadNotFoundError(f"Lead with uid '{lead_uid}' not found.")
        lead_id = lead.id

    entries = await audit_repo.list_audit_entries(lead_id=lead_id, limit=limit, offset=offset)
    return [AuditLogEntryResponse.model_validate(item) for item in entries]
