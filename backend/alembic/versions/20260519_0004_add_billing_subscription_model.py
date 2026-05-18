"""Add billing and subscription data model.

Revision ID: 20260519_0004
Revises: 20260507_0003
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260519_0004"
down_revision: str | None = "20260507_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
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


def upgrade() -> None:
    op.create_table(
        "billing_plan",
        _uuid_pk(),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billing_period", sa.String(length=32), nullable=False),
        sa.Column("trial_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("trial_days >= 0", name="ck_billing_plan_trial_days"),
        sa.UniqueConstraint("code", name="uq_billing_plan_code"),
    )

    op.create_table(
        "billing_price",
        _uuid_pk(),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_price_id", sa.String(length=255), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("billing_period", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("amount_minor >= 0", name="ck_billing_price_amount"),
        sa.CheckConstraint(
            "char_length(currency) = 3",
            name="ck_billing_price_currency",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plan.id"],
            name="fk_billing_price_plan_id_billing_plan",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_price_id",
            name="uq_billing_price_provider_price",
        ),
    )
    op.create_index("ix_billing_price_plan_id", "billing_price", ["plan_id"])

    op.create_table(
        "plan_entitlement",
        _uuid_pk(),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_code", sa.String(length=64), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=True),
        sa.Column("reset_period", sa.String(length=32), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plan.id"],
            name="fk_plan_entitlement_plan_id_billing_plan",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "plan_id",
            "feature_code",
            name="uq_plan_entitlement_plan_feature",
        ),
    )
    op.create_index(
        "ix_plan_entitlement_plan_id",
        "plan_entitlement",
        ["plan_id"],
    )

    op.create_table(
        "billing_customer",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_billing_customer_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_billing_customer_user",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_customer_id",
            name="uq_billing_customer_provider_customer",
        ),
    )
    op.create_index("ix_billing_customer_user_id", "billing_customer", ["user_id"])

    op.create_table(
        "user_subscription",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_billing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "renewal_retry_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.Column("provider_mandate_id", sa.String(length=255), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN "
            "('trialing', 'active', 'past_due', 'canceled', 'expired', 'paused')",
            name="ck_user_subscription_status",
        ),
        sa.ForeignKeyConstraint(
            ["billing_customer_id"],
            ["billing_customer.id"],
            name="fk_user_subscription_billing_customer_id_billing_customer",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plan.id"],
            name="fk_user_subscription_plan_id_billing_plan",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_subscription_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_subscription_id",
            name="uq_user_subscription_provider_subscription",
        ),
    )
    op.create_index("ix_user_subscription_user_id", "user_subscription", ["user_id"])
    op.create_index("ix_user_subscription_plan_id", "user_subscription", ["plan_id"])
    op.create_index(
        "ix_user_subscription_billing_customer_id",
        "user_subscription",
        ["billing_customer_id"],
    )
    op.create_index(
        "ix_user_subscription_status",
        "user_subscription",
        ["status"],
    )
    op.create_index(
        "uq_user_subscription_one_current_per_user",
        "user_subscription",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('trialing', 'active', 'past_due', 'paused')"
        ),
    )

    op.create_table(
        "usage_event",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feature_code", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_usage_event_quantity"),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["user_subscription.id"],
            name="fk_usage_event_subscription_id_user_subscription",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_usage_event_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "feature_code",
            "idempotency_key",
            name="uq_usage_event_user_feature_idempotency",
        ),
    )
    op.create_index("ix_usage_event_user_id", "usage_event", ["user_id"])
    op.create_index("ix_usage_event_subscription_id", "usage_event", ["subscription_id"])
    op.create_index("ix_usage_event_feature_code", "usage_event", ["feature_code"])

    op.create_table(
        "payment_checkout_session",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_session_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("success_url", sa.String(length=2048), nullable=True),
        sa.Column("cancel_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('created', 'redirected', 'completed', 'expired', 'canceled')",
            name="ck_payment_checkout_session_status",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plan.id"],
            name="fk_payment_checkout_session_plan_id_billing_plan",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["price_id"],
            ["billing_price.id"],
            name="fk_payment_checkout_session_price_id_billing_price",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_payment_checkout_session_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_session_id",
            name="uq_payment_checkout_session_provider_session",
        ),
    )
    op.create_index(
        "ix_payment_checkout_session_user_id",
        "payment_checkout_session",
        ["user_id"],
    )
    op.create_index(
        "ix_payment_checkout_session_plan_id",
        "payment_checkout_session",
        ["plan_id"],
    )
    op.create_index(
        "ix_payment_checkout_session_price_id",
        "payment_checkout_session",
        ["price_id"],
    )
    op.create_index(
        "ix_payment_checkout_session_status",
        "payment_checkout_session",
        ["status"],
    )

    op.create_table(
        "payment_transaction",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checkout_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "amount_minor >= 0",
            name="ck_payment_transaction_amount",
        ),
        sa.CheckConstraint(
            "status IN "
            "('pending', 'succeeded', 'failed', 'canceled', 'refunded', 'chargeback')",
            name="ck_payment_transaction_status",
        ),
        sa.ForeignKeyConstraint(
            ["checkout_session_id"],
            ["payment_checkout_session.id"],
            name="fk_payment_tx_checkout_session",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["user_subscription.id"],
            name="fk_payment_transaction_subscription_id_user_subscription",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_payment_transaction_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_payment_id",
            name="uq_payment_transaction_provider_payment",
        ),
    )
    op.create_index(
        "ix_payment_transaction_user_id",
        "payment_transaction",
        ["user_id"],
    )
    op.create_index(
        "ix_payment_transaction_subscription_id",
        "payment_transaction",
        ["subscription_id"],
    )
    op.create_index(
        "ix_payment_transaction_checkout_session_id",
        "payment_transaction",
        ["checkout_session_id"],
    )
    op.create_index(
        "ix_payment_transaction_status",
        "payment_transaction",
        ["status"],
    )

    op.create_table(
        "payment_provider_event",
        _uuid_pk(),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "processing_status IN ('received', 'processed', 'ignored', 'failed')",
            name="ck_payment_provider_event_processing_status",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_payment_provider_event_provider_event",
        ),
    )
    op.create_index(
        "ix_payment_provider_event_processing_status",
        "payment_provider_event",
        ["processing_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_provider_event_processing_status",
        table_name="payment_provider_event",
    )
    op.drop_table("payment_provider_event")

    op.drop_index("ix_payment_transaction_status", table_name="payment_transaction")
    op.drop_index(
        "ix_payment_transaction_checkout_session_id",
        table_name="payment_transaction",
    )
    op.drop_index(
        "ix_payment_transaction_subscription_id",
        table_name="payment_transaction",
    )
    op.drop_index("ix_payment_transaction_user_id", table_name="payment_transaction")
    op.drop_table("payment_transaction")

    op.drop_index(
        "ix_payment_checkout_session_status",
        table_name="payment_checkout_session",
    )
    op.drop_index(
        "ix_payment_checkout_session_price_id",
        table_name="payment_checkout_session",
    )
    op.drop_index(
        "ix_payment_checkout_session_plan_id",
        table_name="payment_checkout_session",
    )
    op.drop_index(
        "ix_payment_checkout_session_user_id",
        table_name="payment_checkout_session",
    )
    op.drop_table("payment_checkout_session")

    op.drop_index("ix_usage_event_feature_code", table_name="usage_event")
    op.drop_index("ix_usage_event_subscription_id", table_name="usage_event")
    op.drop_index("ix_usage_event_user_id", table_name="usage_event")
    op.drop_table("usage_event")

    op.drop_index(
        "uq_user_subscription_one_current_per_user",
        table_name="user_subscription",
    )
    op.drop_index("ix_user_subscription_status", table_name="user_subscription")
    op.drop_index(
        "ix_user_subscription_billing_customer_id",
        table_name="user_subscription",
    )
    op.drop_index("ix_user_subscription_plan_id", table_name="user_subscription")
    op.drop_index("ix_user_subscription_user_id", table_name="user_subscription")
    op.drop_table("user_subscription")

    op.drop_index("ix_billing_customer_user_id", table_name="billing_customer")
    op.drop_table("billing_customer")

    op.drop_index("ix_plan_entitlement_plan_id", table_name="plan_entitlement")
    op.drop_table("plan_entitlement")

    op.drop_index("ix_billing_price_plan_id", table_name="billing_price")
    op.drop_table("billing_price")
    op.drop_table("billing_plan")
