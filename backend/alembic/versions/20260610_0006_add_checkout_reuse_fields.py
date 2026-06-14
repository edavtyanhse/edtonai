"""Add checkout reuse and provider order fields.

Revision ID: 20260610_0006
Revises: 20260524_0005
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260610_0006"
down_revision: str | None = "20260524_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payment_checkout_session",
        sa.Column("provider_order_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payment_checkout_session",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "payment_checkout_session",
        sa.Column("payment_url", sa.String(length=2048), nullable=True),
    )
    op.create_unique_constraint(
        "uq_payment_checkout_session_provider_order",
        "payment_checkout_session",
        ["provider", "provider_order_id"],
    )
    op.create_index(
        "ix_payment_checkout_session_reusable",
        "payment_checkout_session",
        ["user_id", "plan_id", "price_id", "provider", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_checkout_session_reusable",
        table_name="payment_checkout_session",
    )
    op.drop_constraint(
        "uq_payment_checkout_session_provider_order",
        "payment_checkout_session",
        type_="unique",
    )
    op.drop_column("payment_checkout_session", "payment_url")
    op.drop_column("payment_checkout_session", "idempotency_key")
    op.drop_column("payment_checkout_session", "provider_order_id")
