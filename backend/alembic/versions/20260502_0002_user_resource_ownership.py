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


def _ensure_historical_baseline_tables() -> None:
    """Create the historical pre-Alembic schema for brand-new databases.

    Existing production databases already had this schema before Alembic was
    introduced. New empty databases need the same baseline before post-baseline
    revisions can safely add ownership, hardening, and billing tables.
    """
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(320) NOT NULL UNIQUE,
            password_hash VARCHAR(255),
            is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            device_info VARCHAR(512)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id "
        "ON refresh_tokens (user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(128) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_email_verifications_token "
        "ON email_verifications (token)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS oauth_accounts (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider VARCHAR(50) NOT NULL,
            provider_user_id VARCHAR(255) NOT NULL,
            email VARCHAR(320),
            name VARCHAR(255),
            avatar_url VARCHAR(1024),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_oauth_provider_uid UNIQUE (provider, provider_user_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_oauth_accounts_user_id "
        "ON oauth_accounts (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_oauth_accounts_provider_user_id "
        "ON oauth_accounts (provider_user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_raw (
            id UUID PRIMARY KEY,
            source_text TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL UNIQUE,
            personal_info JSONB,
            summary TEXT,
            skills JSONB DEFAULT '[]',
            work_experience JSONB DEFAULT '[]',
            education JSONB DEFAULT '[]',
            certifications JSONB DEFAULT '[]',
            languages JSONB DEFAULT '[]',
            raw_sections JSONB DEFAULT '{}',
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            parsed_at TIMESTAMP WITHOUT TIME ZONE
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_raw_content_hash "
        "ON resume_raw (content_hash)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_raw_updated_at "
        "ON resume_raw (updated_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vacancy_raw (
            id UUID PRIMARY KEY,
            source_text TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL UNIQUE,
            source_url VARCHAR(2048),
            job_title VARCHAR(255),
            company VARCHAR(255),
            employment_type VARCHAR(100),
            location VARCHAR(255),
            required_skills JSONB DEFAULT '[]',
            preferred_skills JSONB DEFAULT '[]',
            experience_requirements JSONB,
            responsibilities JSONB DEFAULT '[]',
            ats_keywords JSONB DEFAULT '[]',
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            parsed_at TIMESTAMP WITHOUT TIME ZONE
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vacancy_raw_content_hash "
        "ON vacancy_raw (content_hash)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vacancy_raw_updated_at "
        "ON vacancy_raw (updated_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_result (
            id UUID PRIMARY KEY,
            operation VARCHAR(100) NOT NULL,
            input_hash VARCHAR(64) NOT NULL,
            output_json JSONB NOT NULL,
            model VARCHAR(255),
            provider VARCHAR(100),
            error TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_result_input_hash "
        "ON ai_result (input_hash)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_result_operation_input_hash "
        "ON ai_result (operation, input_hash)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_result_updated_at "
        "ON ai_result (updated_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_version (
            id UUID PRIMARY KEY,
            resume_id UUID NOT NULL REFERENCES resume_raw(id) ON DELETE CASCADE,
            vacancy_id UUID NOT NULL REFERENCES vacancy_raw(id) ON DELETE CASCADE,
            parent_version_id UUID REFERENCES resume_version(id) ON DELETE SET NULL,
            text TEXT NOT NULL,
            change_log JSONB NOT NULL DEFAULT '[]',
            selected_checkbox_ids JSONB NOT NULL DEFAULT '[]',
            analysis_id UUID REFERENCES ai_result(id) ON DELETE SET NULL,
            provider VARCHAR(100),
            model VARCHAR(255),
            prompt_version VARCHAR(50),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_version_resume_id "
        "ON resume_version (resume_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_version_vacancy_id "
        "ON resume_version (vacancy_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_version_parent_version_id "
        "ON resume_version (parent_version_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_version (
            id UUID PRIMARY KEY,
            user_id VARCHAR(255),
            type VARCHAR(20) NOT NULL,
            analysis_id UUID REFERENCES ai_result(id) ON DELETE SET NULL,
            title VARCHAR(255),
            resume_text TEXT NOT NULL,
            vacancy_text TEXT NOT NULL,
            result_text TEXT NOT NULL,
            change_log JSONB NOT NULL DEFAULT '[]',
            selected_checkbox_ids JSONB NOT NULL DEFAULT '[]',
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_version_user_id "
        "ON user_version (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_version_analysis_id "
        "ON user_version (analysis_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ideal_resume (
            id UUID PRIMARY KEY,
            vacancy_id UUID NOT NULL REFERENCES vacancy_raw(id) ON DELETE CASCADE,
            vacancy_hash VARCHAR(64) NOT NULL,
            text TEXT NOT NULL,
            generation_metadata JSONB NOT NULL DEFAULT '{}',
            options JSONB NOT NULL DEFAULT '{}',
            input_hash VARCHAR(64) NOT NULL UNIQUE,
            provider VARCHAR(50),
            model VARCHAR(100),
            prompt_version VARCHAR(50),
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ideal_resume_vacancy_id "
        "ON ideal_resume (vacancy_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ideal_resume_vacancy_hash "
        "ON ideal_resume (vacancy_hash)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ideal_resume_input_hash "
        "ON ideal_resume (input_hash)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR NOT NULL,
            feedback_text TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            metric_type VARCHAR(16) NOT NULL DEFAULT 'csat',
            score INTEGER NOT NULL DEFAULT 5,
            context_step VARCHAR(64),
            ui_variant VARCHAR(16),
            user_segment VARCHAR(64)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_user_email "
        "ON feedback (user_email)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_created_at "
        "ON feedback (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_metric_type "
        "ON feedback (metric_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_context_step "
        "ON feedback (context_step)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_ui_variant "
        "ON feedback (ui_variant)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_user_segment "
        "ON feedback (user_segment)"
    )


def upgrade() -> None:
    _ensure_historical_baseline_tables()

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
