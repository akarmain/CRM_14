"""create contacts table

Revision ID: 0001_create_contacts
Revises: 
Create Date: 2025-01-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_create_contacts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("middle_name", sa.String(length=120), nullable=False),
        sa.Column("photo", sa.String(length=512), nullable=False),
        sa.Column("extra_fields", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("contacts")
