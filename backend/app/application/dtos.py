from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.entities import Lead
from app.domain.enums import LeadStage, Users


@dataclass(slots=True)
class LeadStageCommentInfo:
    author: Users
    comment: str | None


@dataclass(slots=True)
class LeadStageInfo:
    stage: LeadStage
    entered_at: datetime
    left_at: datetime | None
    approved: bool
    comment: list[LeadStageCommentInfo]


@dataclass(slots=True)
class LeadWithStageInfo:
    lead: Lead
    stage_info: list[LeadStageInfo]
