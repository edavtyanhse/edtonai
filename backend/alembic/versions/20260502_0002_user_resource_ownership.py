"""Add user ownership mappings for raw resources and versions.

Revision ID: 20260502_0002
Revises: 20260429_0001
Create Date: 2026-05-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260502_0002"
down_revision: str | None = "20260429_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_resume",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resume_raw.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "resume_id",
            name="uq_user_resume_owner_record",
        ),
    )
    op.create_index("ix_user_resume_resume_id", "user_resume", ["resume_id"])
    op.create_index("ix_user_resume_user_id", "user_resume", ["user_id"])

    op.create_table(
        "user_vacancy",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancy_raw.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "vacancy_id",
            name="uq_user_vacancy_owner_record",
        ),
    )
    op.create_index("ix_user_vacancy_vacancy_id", "user_vacancy", ["vacancy_id"])
    op.create_index("ix_user_vacancy_user_id", "user_vacancy", ["user_id"])

    op.add_column("resume_version", sa.Column("user_id", sa.String(length=255)))
    op.create_index("ix_resume_version_user_id", "resume_version", ["user_id"])

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
