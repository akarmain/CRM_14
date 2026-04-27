from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import LeadStage, ReturnRequestStatus, SourcesCode, Users
from app.infrastructure.sql.db import Base


class LeadModel(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_uid: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    source_code: Mapped[SourcesCode] = mapped_column(
        Enum(SourcesCode, name="sources_code"),
        nullable=False,
    )
    current_stage: Mapped[LeadStage] = mapped_column(
        Enum(LeadStage, name="lead_stage"),
        nullable=False,
        default=LeadStage.new,
    )
    owner: Mapped[Users] = mapped_column(Enum(Users, name="users"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class LeadStageEventModel(Base):
    __tablename__ = "leads_stage"
    __table_args__ = (
        Index("ix_leads_stage_lead_id_entered_at", "lead_id", "entered_at"),
        UniqueConstraint("lead_id", "stage", "entered_at", name="uq_leads_stage_lead_stage_entered_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[LeadStage] = mapped_column(Enum(LeadStage, name="lead_stage"), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved: Mapped[bool] = mapped_column(nullable=False, default=True)


class LeadCommentModel(Base):
    __tablename__ = "leads_comments"
    __table_args__ = (UniqueConstraint("stage_event_id", name="uq_leads_comments_stage_event_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stage_event_id: Mapped[int] = mapped_column(
        ForeignKey("leads_stage.id", ondelete="CASCADE"),
        nullable=False,
    )
    author: Mapped[Users] = mapped_column(Enum(Users, name="users"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StageReturnRequestModel(Base):
    __tablename__ = "stage_return_requests"
    __table_args__ = (
        Index("ix_stage_return_requests_status_requested_at", "status", "requested_at"),
        Index("ix_stage_return_requests_lead_id_requested_at", "lead_id", "requested_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[LeadStage] = mapped_column(Enum(LeadStage, name="lead_stage"), nullable=False)
    to_stage: Mapped[LeadStage] = mapped_column(Enum(LeadStage, name="lead_stage"), nullable=False)
    requested_by: Mapped[Users] = mapped_column(Enum(Users, name="users"), nullable=False)
    request_comment: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ReturnRequestStatus] = mapped_column(
        Enum(ReturnRequestStatus, name="return_request_status"),
        nullable=False,
        default=ReturnRequestStatus.pending,
    )
    reviewed_by: Mapped[Users | None] = mapped_column(Enum(Users, name="users"), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_lead_id_created_at", "lead_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
