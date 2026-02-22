"""add approval tasks table

Revision ID: 20260222_0002
Revises: 20260222_0001
Create Date: 2026-02-22 00:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260222_0002"
down_revision = "20260222_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_tasks",
        sa.Column("approval_task_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("ticket_id", sa.String(length=64), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_reason", sa.Text(), nullable=False),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolver_id", sa.String(length=64), nullable=True),
        sa.Column("token_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_approval_tasks_run_id", "approval_tasks", ["run_id"])
    op.create_index("ix_approval_tasks_ticket_id", "approval_tasks", ["ticket_id"])
    op.create_index("ix_approval_tasks_action_type", "approval_tasks", ["action_type"])
    op.create_index("ix_approval_tasks_status", "approval_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_approval_tasks_status", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_action_type", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_ticket_id", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_run_id", table_name="approval_tasks")
    op.drop_table("approval_tasks")
