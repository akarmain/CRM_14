"""initial postgres schema with approvals and audit

Revision ID: 20260406_0001
Revises:
Create Date: 2026-04-06 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_0001"
down_revision = None
branch_labels = None
depends_on = None


users_enum = postgresql.ENUM("manager_1", "manager_2", "sales_head", name="users", create_type=False)
lead_stage_enum = postgresql.ENUM("new", "qualified", "proposal", "won", "lost", name="lead_stage", create_type=False)
sources_code_enum = postgresql.ENUM(
    "advertisement",
    "website",
    "recommendation",
    "event",
    "other",
    name="sources_code",
    create_type=False,
)
return_request_status_enum = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="return_request_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    users_enum.create(bind, checkfirst=True)
    lead_stage_enum.create(bind, checkfirst=True)
    sources_code_enum.create(bind, checkfirst=True)
    return_request_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "leads",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_uid", sa.String(length=32), nullable=False),
        sa.Column("source_code", sources_code_enum, nullable=False),
        sa.Column("current_stage", lead_stage_enum, nullable=False, server_default="new"),
        sa.Column("owner", users_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("lead_uid", name="uq_leads_lead_uid"),
    )

    op.create_table(
        "leads_stage",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", lead_stage_enum, nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("lead_id", "stage", "entered_at", name="uq_leads_stage_lead_stage_entered_at"),
    )
    op.create_index("ix_leads_stage_lead_id_entered_at", "leads_stage", ["lead_id", "entered_at"])

    op.create_table(
        "leads_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("stage_event_id", sa.BigInteger(), sa.ForeignKey("leads_stage.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author", users_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("stage_event_id", name="uq_leads_comments_stage_event_id"),
    )

    op.create_table(
        "stage_return_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_stage", lead_stage_enum, nullable=False),
        sa.Column("to_stage", lead_stage_enum, nullable=False),
        sa.Column("requested_by", users_enum, nullable=False),
        sa.Column("request_comment", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", return_request_status_enum, nullable=False, server_default="pending"),
        sa.Column("reviewed_by", users_enum, nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_stage_return_requests_status_requested_at",
        "stage_return_requests",
        ["status", "requested_at"],
    )
    op.create_index(
        "ix_stage_return_requests_lead_id_requested_at",
        "stage_return_requests",
        ["lead_id", "requested_at"],
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_log_lead_id_created_at", "audit_log", ["lead_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_lead_id_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_stage_return_requests_lead_id_requested_at", table_name="stage_return_requests")
    op.drop_index("ix_stage_return_requests_status_requested_at", table_name="stage_return_requests")
    op.drop_table("stage_return_requests")

    op.drop_table("leads_comments")
    op.drop_index("ix_leads_stage_lead_id_entered_at", table_name="leads_stage")
    op.drop_table("leads_stage")
    op.drop_table("leads")

    bind = op.get_bind()
    return_request_status_enum.drop(bind, checkfirst=True)
    sources_code_enum.drop(bind, checkfirst=True)
    lead_stage_enum.drop(bind, checkfirst=True)
    users_enum.drop(bind, checkfirst=True)
