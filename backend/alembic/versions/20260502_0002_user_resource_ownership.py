"""Add user ownership mappings for raw resources and versions.

Revision ID: 20260502_0002
Revises: 20260429_0001
Create Date: 2026-05-02
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260502_0002"
down_revision: str | None = "20260429_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Production databases may already contain these tables from the historical
    # SQL baseline or DB_AUTO_CREATE. Keep the first Alembic delta idempotent so
    # previously unstamped databases can still reach current revisions safely.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_resume (
            id UUID PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            resume_id UUID NOT NULL REFERENCES resume_raw(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            CONSTRAINT uq_user_resume_owner_record UNIQUE (user_id, resume_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_resume_resume_id "
        "ON user_resume (resume_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_resume_user_id "
        "ON user_resume (user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_vacancy (
            id UUID PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            vacancy_id UUID NOT NULL REFERENCES vacancy_raw(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            CONSTRAINT uq_user_vacancy_owner_record UNIQUE (user_id, vacancy_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_vacancy_vacancy_id "
        "ON user_vacancy (vacancy_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_vacancy_user_id "
        "ON user_vacancy (user_id)"
    )

    op.execute("ALTER TABLE resume_version ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_version_user_id "
        "ON resume_version (user_id)"
    )

    op.execute("UPDATE user_version SET user_id = 'legacy-anonymous' WHERE user_id IS NULL")
    op.alter_column("user_version", "user_id", nullable=False)


def downgrade() -> None:
    op.alter_column("user_version", "user_id", nullable=True)
    op.drop_index("ix_resume_version_user_id", table_name="resume_version")
    op.drop_column("resume_version", "user_id")
    op.drop_index("ix_user_vacancy_user_id", table_name="user_vacancy")
    op.drop_index("ix_user_vacancy_vacancy_id", table_name="user_vacancy")
    op.drop_table("user_vacancy")
    op.drop_index("ix_user_resume_user_id", table_name="user_resume")
    op.drop_index("ix_user_resume_resume_id", table_name="user_resume")
    op.drop_table("user_resume")
