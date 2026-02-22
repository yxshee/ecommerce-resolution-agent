"""initial tables

Revision ID: 20260222_0001
Revises:
Create Date: 2026-02-22 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260222_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("ticket_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("issue_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])
    op.create_index("ix_tickets_order_id", "tickets", ["order_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])

    op.create_table(
        "cases",
        sa.Column("case_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("ticket_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("decision_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_cases_ticket_id", "cases", ["ticket_id"])
    op.create_index("ix_cases_run_id", "cases", ["run_id"], unique=True)

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("actor_agent", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("tool_input_redacted_json", sa.JSON(), nullable=True),
        sa.Column("tool_output_redacted_json", sa.JSON(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_events_run_id", "audit_events", ["run_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])

    op.create_table(
        "actions",
        sa.Column("action_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=128), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("simulation_mode", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approval_task_id", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_actions_run_id", "actions", ["run_id"])
    op.create_index("ix_actions_status", "actions", ["status"])
    op.create_index("ix_actions_customer_id", "actions", ["customer_id"])
    op.create_index("ix_actions_order_id", "actions", ["order_id"])
    op.create_index("ix_actions_idempotency_key", "actions", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_actions_idempotency_key", table_name="actions")
    op.drop_index("ix_actions_order_id", table_name="actions")
    op.drop_index("ix_actions_customer_id", table_name="actions")
    op.drop_index("ix_actions_status", table_name="actions")
    op.drop_index("ix_actions_run_id", table_name="actions")
    op.drop_table("actions")

    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_run_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_cases_run_id", table_name="cases")
    op.drop_index("ix_cases_ticket_id", table_name="cases")
    op.drop_table("cases")

    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_order_id", table_name="tickets")
    op.drop_index("ix_tickets_customer_id", table_name="tickets")
    op.drop_table("tickets")
