"""Prepare billing provider foundation.

Revision ID: 20260524_0005
Revises: 20260519_0004
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260524_0005"
down_revision: str | None = "20260519_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )


def upgrade() -> None:
    op.add_column(
        "payment_transaction",
        sa.Column("provider_status", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payment_provider_event",
        sa.Column("provider_status", sa.String(length=64), nullable=True),
    )

    op.drop_constraint(
        "ck_payment_transaction_status",
        "payment_transaction",
        type_="check",
    )
    op.create_check_constraint(
        "ck_payment_transaction_status",
        "payment_transaction",
        "status IN ("
        "'pending', 'authorized', 'succeeded', 'failed', 'canceled', "
        "'partially_canceled', 'refunded', 'partially_refunded', "
        "'chargeback', 'unknown'"
        ")",
    )

    op.create_table(
        "billing_audit_log",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "payment_transaction_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "payment_provider_event_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("old_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["payment_provider_event_id"],
            ["payment_provider_event.id"],
            name="fk_billing_audit_log_provider_event_id_payment_provider_event",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["payment_transaction_id"],
            ["payment_transaction.id"],
            name="fk_billing_audit_log_payment_transaction_id_payment_transaction",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["user_subscription.id"],
            name="fk_billing_audit_log_subscription_id_user_subscription",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_billing_audit_log_user_id_users",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_billing_audit_log_user_id", "billing_audit_log", ["user_id"])
    op.create_index(
        "ix_billing_audit_log_subscription_id",
        "billing_audit_log",
        ["subscription_id"],
    )
    op.create_index(
        "ix_billing_audit_log_payment_transaction_id",
        "billing_audit_log",
        ["payment_transaction_id"],
    )
    op.create_index(
        "ix_billing_audit_log_payment_provider_event_id",
        "billing_audit_log",
        ["payment_provider_event_id"],
    )
    op.create_index("ix_billing_audit_log_action", "billing_audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_billing_audit_log_action", table_name="billing_audit_log")
    op.drop_index(
        "ix_billing_audit_log_payment_provider_event_id",
        table_name="billing_audit_log",
    )
    op.drop_index(
        "ix_billing_audit_log_payment_transaction_id",
        table_name="billing_audit_log",
    )
    op.drop_index(
        "ix_billing_audit_log_subscription_id",
        table_name="billing_audit_log",
    )
    op.drop_index("ix_billing_audit_log_user_id", table_name="billing_audit_log")
    op.drop_table("billing_audit_log")

    op.drop_constraint(
        "ck_payment_transaction_status",
        "payment_transaction",
        type_="check",
    )
    op.create_check_constraint(
        "ck_payment_transaction_status",
        "payment_transaction",
        "status IN ("
        "'pending', 'succeeded', 'failed', 'canceled', 'refunded', 'chargeback'"
        ")",
    )
    op.drop_column("payment_provider_event", "provider_status")
    op.drop_column("payment_transaction", "provider_status")
