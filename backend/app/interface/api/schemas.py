from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import LeadStage, SourcesCode, Users


class LeadCreateRequest(BaseModel):
    source_code: SourcesCode
    owner: Users
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    lead_uid: str | None = None


class NewLeadRequest(BaseModel):
    source_code: SourcesCode
    owner: Users
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class LeadStageInfoItem(BaseModel):
    stage: LeadStage
    entered_at: datetime
    left_at: datetime | None
    approved: bool
    comment: list["StageInfoCommentResponse"] = Field(default_factory=list)


class StageInfoCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author: Users
    comment: str | None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lead_uid: str
    source_code: SourcesCode
    current_stage: LeadStage
    owner: Users
    title: str | None
    notes: str | None


class LeadListResponse(LeadResponse):
    stage_info: list[LeadStageInfoItem]


class MoveStageRequest(BaseModel):
    stage: LeadStage
    comment: str | None = None
    author: Users


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


class MoveStageResponse(BaseModel):
    lead: LeadResponse
    stage_event: StageEventResponse


class HealthResponse(BaseModel):
    status: str
    mode: str
