"""Harden owner-bound data model and token storage.

Revision ID: 20260507_0003
Revises: 20260502_0002
Create Date: 2026-05-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260507_0003"
down_revision: str | None = "20260502_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_USER_ID = "00000000-0000-0000-0000-000000000000"
UUID_REGEX = (
    "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _ensure_legacy_user() -> None:
    op.execute(
        f"""
            INSERT INTO users (
                id,
                email,
                password_hash,
                is_email_verified,
                is_active
            )
            VALUES (
                '{LEGACY_USER_ID}'::uuid,
                'legacy-archive@edtonai.local',
                NULL,
                TRUE,
                FALSE
            )
            ON CONFLICT DO NOTHING
            """
    )


def _cast_user_id_column_to_uuid(table_name: str, nullable: bool = False) -> None:
    op.alter_column(
        table_name,
        "user_id",
        type_=postgresql.UUID(as_uuid=True),
        nullable=nullable,
        postgresql_using=(
            f"CASE "
            f"WHEN user_id IS NOT NULL AND user_id ~* '{UUID_REGEX}' "
            f"THEN user_id::uuid "
            f"ELSE '{LEGACY_USER_ID}'::uuid "
            f"END"
        ),
    )


def _alter_timestamps_to_timestamptz() -> None:
    timestamp_columns = {
        "resume_raw": ["created_at", "updated_at", "parsed_at"],
        "vacancy_raw": ["created_at", "updated_at", "parsed_at"],
        "ai_result": ["created_at", "updated_at"],
        "resume_version": ["created_at", "updated_at"],
        "ideal_resume": ["created_at", "updated_at"],
        "user_version": ["created_at", "updated_at"],
        "feedback": ["created_at"],
        "user_resume": ["created_at", "parsed_at"],
        "user_vacancy": ["created_at", "parsed_at"],
    }
    for table_name, columns in timestamp_columns.items():
        for column_name in columns:
            op.execute(
                sa.text(
                    f"""
                    ALTER TABLE {table_name}
                    ALTER COLUMN {column_name}
                    TYPE TIMESTAMP WITH TIME ZONE
                    USING {column_name} AT TIME ZONE 'UTC'
                    """
                )
            )


def _backfill_token_hashes() -> None:
    op.execute(
        """
        UPDATE refresh_tokens
        SET token_hash = encode(sha256(id::text::bytea), 'hex')
        WHERE token_hash IS NULL
        """
    )
    op.execute(
        """
        UPDATE email_verifications
        SET token_hash = encode(sha256(COALESCE(token, id::text)::bytea), 'hex')
        WHERE token_hash IS NULL
        """
    )


def _backfill_feedback_user_hashes() -> None:
    op.execute(
        """
        UPDATE feedback
        SET user_hash = encode(
                sha256(
                    lower(
                        trim(COALESCE(user_email, 'legacy-feedback:' || id::text))
                    )::bytea
                ),
                'hex'
            ),
            user_email = NULL
        WHERE user_hash IS NULL
        """
    )


def upgrade() -> None:
    _ensure_legacy_user()

    # User-specific parsed overrides keep global raw cache immutable after edits.
    op.add_column(
        "user_resume",
        sa.Column("parsed_data_override", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "user_resume",
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_vacancy",
        sa.Column("parsed_data_override", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "user_vacancy",
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Convert owner columns from strings to real users.id foreign keys.
    _cast_user_id_column_to_uuid("user_resume")
    _cast_user_id_column_to_uuid("user_vacancy")
    _cast_user_id_column_to_uuid("user_version")
    _cast_user_id_column_to_uuid("resume_version")
    op.alter_column("resume_version", "user_id", nullable=False)

    op.create_foreign_key(
        "fk_user_resume_user_id_users",
        "user_resume",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_vacancy_user_id_users",
        "user_vacancy",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_version_user_id_users",
        "user_version",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_resume_version_user_id_users",
        "resume_version",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Store only hashes of bearer secrets going forward.
    op.add_column(
        "refresh_tokens",
        sa.Column("token_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "email_verifications",
        sa.Column("token_hash", sa.String(length=64), nullable=True),
    )
    op.alter_column("email_verifications", "token", nullable=True)
    _backfill_token_hashes()
    op.alter_column("refresh_tokens", "token_hash", nullable=False)
    op.alter_column("email_verifications", "token_hash", nullable=False)
    op.create_index(
        "ix_refresh_tokens_token_hash",
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_email_verifications_token_hash",
        "email_verifications",
        ["token_hash"],
        unique=True,
    )

    # Keep feedback attributable without storing email as the primary identifier.
    op.add_column(
        "feedback",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("feedback", sa.Column("user_hash", sa.String(length=64)))
    _backfill_feedback_user_hashes()
    op.alter_column("feedback", "user_email", nullable=True)
    op.alter_column("feedback", "user_hash", nullable=False)
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_user_hash", "feedback", ["user_hash"])
    op.create_foreign_key(
        "fk_feedback_user_id_users",
        "feedback",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # analysis_link duplicated ai_result cache semantics and had no read-path.
    op.execute("DROP TABLE IF EXISTS analysis_link")

    op.execute("UPDATE user_version SET type = 'adapt' WHERE type NOT IN ('adapt', 'ideal')")
    op.create_check_constraint(
        "ck_user_version_type",
        "user_version",
        "type IN ('adapt', 'ideal')",
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_feedback_metric_type'
            ) THEN
                ALTER TABLE feedback
                    ADD CONSTRAINT ck_feedback_metric_type
                    CHECK (metric_type IN ('csat', 'nps'));
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_feedback_score_by_metric'
            ) THEN
                ALTER TABLE feedback
                    ADD CONSTRAINT ck_feedback_score_by_metric
                    CHECK (
                        (metric_type = 'csat' AND score BETWEEN 1 AND 5)
                        OR (metric_type = 'nps' AND score BETWEEN 0 AND 10)
                    );
            END IF;
        END $$;
        """
    )

    _alter_timestamps_to_timestamptz()


def downgrade() -> None:
    op.drop_constraint("ck_user_version_type", "user_version", type_="check")
    op.create_table(
        "analysis_link",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resume_raw.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancy_raw.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["analysis_result_id"],
            ["ai_result.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_link_resume_id", "analysis_link", ["resume_id"])
    op.create_index("ix_analysis_link_vacancy_id", "analysis_link", ["vacancy_id"])
    op.create_index(
        "ix_analysis_link_analysis_result_id",
        "analysis_link",
        ["analysis_result_id"],
    )

    op.drop_constraint("fk_feedback_user_id_users", "feedback", type_="foreignkey")
    op.drop_index("ix_feedback_user_hash", table_name="feedback")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.execute(
        """
        UPDATE feedback
        SET user_email = COALESCE(user_email, user_hash)
        WHERE user_email IS NULL
        """
    )
    op.drop_column("feedback", "user_hash")
    op.drop_column("feedback", "user_id")
    op.alter_column("feedback", "user_email", nullable=False)

    op.drop_index("ix_email_verifications_token_hash", table_name="email_verifications")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_column("email_verifications", "token_hash")
    op.drop_column("refresh_tokens", "token_hash")
    op.alter_column("email_verifications", "token", nullable=False)

    op.drop_constraint(
        "fk_resume_version_user_id_users",
        "resume_version",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_version_user_id_users",
        "user_version",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_vacancy_user_id_users",
        "user_vacancy",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_resume_user_id_users",
        "user_resume",
        type_="foreignkey",
    )
    op.alter_column("resume_version", "user_id", nullable=True)
    for table_name in ("resume_version", "user_version", "user_vacancy", "user_resume"):
        op.alter_column(
            table_name,
            "user_id",
            type_=sa.String(length=255),
            postgresql_using="user_id::text",
        )

    op.drop_column("user_vacancy", "parsed_at")
    op.drop_column("user_vacancy", "parsed_data_override")
    op.drop_column("user_resume", "parsed_at")
    op.drop_column("user_resume", "parsed_data_override")
