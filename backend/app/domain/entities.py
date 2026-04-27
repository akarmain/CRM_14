from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import AppRole, LeadStage, ReturnRequestStatus, SourcesCode, Users


@dataclass(slots=True)
class Lead:
    id: int
    lead_uid: str
    source_code: SourcesCode
    current_stage: LeadStage
    owner: Users
    title: str | None
    notes: str | None


@dataclass(slots=True)
class LeadStageEvent:
    id: int
    lead_id: int
    stage: LeadStage
    entered_at: datetime
    left_at: datetime | None
    approved: bool


@dataclass(slots=True)
class LeadComment:
    id: int
    stage_event_id: int
    author: Users
    comment: str | None
    created_at: datetime


@dataclass(slots=True)
class StageReturnRequest:
    id: int
    lead_id: int
    from_stage: LeadStage
    to_stage: LeadStage
    requested_by: Users
    request_comment: str
    requested_at: datetime
    status: ReturnRequestStatus
    reviewed_by: Users | None
    review_comment: str | None
    reviewed_at: datetime | None


@dataclass(slots=True)
class AuditLogEntry:
    id: int
    lead_id: int | None
    actor_role: AppRole
    action_type: str
    payload_json: dict
    created_at: datetime
