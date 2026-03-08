from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import LeadStage, SourcesCode, Users


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
