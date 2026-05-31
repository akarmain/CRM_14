from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import AppRole, LeadStage, ReturnRequestStatus, SourcesCode, Users


class SessionRoleRequest(BaseModel):
    role: AppRole


class SessionMeResponse(BaseModel):
    role: AppRole
    role_label: str
    permissions: dict[str, bool]


class NewLeadRequest(BaseModel):
    source_code: SourcesCode = SourcesCode.other
    owner: Users | None = None
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class LeadUpdateRequest(BaseModel):
    owner: Users | None = None
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_payload(self) -> "LeadUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        if "owner" in self.model_fields_set and self.owner is None:
            raise ValueError("owner cannot be null")
        return self


class MoveStageRequest(BaseModel):
    stage: LeadStage
    comment: str | None = None


class CreateReturnRequest(BaseModel):
    comment: str = Field(min_length=1)


class ReviewReturnRequest(BaseModel):
    review_comment: str = Field(min_length=1)


class StageInfoCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author: Users
    comment: str | None


class LeadStageInfoItem(BaseModel):
    stage: LeadStage
    entered_at: datetime
    left_at: datetime | None
    approved: bool
    comment: list[StageInfoCommentResponse] = Field(default_factory=list)


class StageCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author: Users
    comment: str | None
    created_at: datetime


class StageEventResponse(BaseModel):
    id: int
    stage: LeadStage
    entered_at: datetime
    left_at: datetime | None
    approved: bool
    comment: StageCommentResponse | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lead_uid: str
    source_code: SourcesCode
    current_stage: LeadStage
    owner: Users
    title: str | None
    notes: str | None
    created_at: datetime | None = None


class ReturnRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    lead_uid: str | None = None
    from_stage: LeadStage
    to_stage: LeadStage
    requested_by: Users
    request_comment: str
    requested_at: datetime
    status: ReturnRequestStatus
    reviewed_by: Users | None
    review_comment: str | None
    reviewed_at: datetime | None


class AuditLogEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int | None
    actor_role: AppRole
    action_type: str
    payload_json: dict[str, Any]
    created_at: datetime


class LeadListResponse(LeadResponse):
    stage_info: list[LeadStageInfoItem]
    pending_return_requests: int = 0


class LeadDetailResponse(LeadListResponse):
    return_requests: list[ReturnRequestResponse] = Field(default_factory=list)
    audit_entries: list[AuditLogEntryResponse] = Field(default_factory=list)


class MoveStageResponse(BaseModel):
    lead: LeadResponse
    stage_event: StageEventResponse


class ImportLeadsResponse(BaseModel):
    created: int
    lead_uids: list[str]
    skipped: int = 0
    skipped_lead_uids: list[str] = Field(default_factory=list)


class FunnelCountResponse(BaseModel):
    stage: LeadStage
    count: int


class ConversionResponse(BaseModel):
    from_stage: LeadStage
    to_stage: LeadStage
    from_count: int
    to_count: int
    rate: float


class StageDurationResponse(BaseModel):
    stage: LeadStage
    average_seconds: float
    average_hours: float


class ReportsSummaryResponse(BaseModel):
    total_leads: int
    counts: list[FunnelCountResponse]
    conversions: list[ConversionResponse]
    average_stage_durations: list[StageDurationResponse]


class HealthResponse(BaseModel):
    status: str
    mode: str


class LeadsFilterQuery(BaseModel):
    owner: Users | None = None
    stage: LeadStage | None = None
    source_code: SourcesCode | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
