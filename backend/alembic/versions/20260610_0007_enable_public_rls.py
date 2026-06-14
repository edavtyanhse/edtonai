"""Enable RLS for public tables exposed by Supabase Data API.

Revision ID: 20260610_0007
Revises: 20260610_0006
Create Date: 2026-06-10
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260610_0007"
down_revision: str | None = "20260610_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PUBLIC_TABLES = (
    "alembic_version",
    "users",
    "oauth_accounts",
    "refresh_tokens",
    "email_verifications",
    "resume_raw",
    "vacancy_raw",
    "ai_result",
    "resume_version",
    "ideal_resume",
    "user_version",
    "feedback",
    "user_resume",
    "user_vacancy",
    "billing_plan",
    "billing_price",
    "plan_entitlement",
    "billing_customer",
    "user_subscription",
    "usage_event",
    "payment_checkout_session",
    "payment_transaction",
    "payment_provider_event",
    "billing_audit_log",
)


def upgrade() -> None:
    for table_name in PUBLIC_TABLES:
        op.execute(f"ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY")

    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public "
        "FROM anon, authenticated"
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public "
        "FROM anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE USAGE, SELECT ON SEQUENCES FROM anon, authenticated"
    )
    op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon, authenticated"
    )
    op.execute(
        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public "
        "TO anon, authenticated"
    )
    op.execute(
        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon, authenticated"
    )
    for table_name in PUBLIC_TABLES:
        op.execute(f"ALTER TABLE public.{table_name} DISABLE ROW LEVEL SECURITY")
    op.execute("NOTIFY pgrst, 'reload schema'")
