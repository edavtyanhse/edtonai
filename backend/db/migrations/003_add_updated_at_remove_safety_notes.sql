-- Migration: Add updated_at to all tables, remove safety_notes from resume_version
-- Created: 2026-01-11

-- Add updated_at to resume_raw
ALTER TABLE resume_raw
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to vacancy_raw
ALTER TABLE vacancy_raw
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to ai_result
ALTER TABLE ai_result
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to analysis_link
ALTER TABLE analysis_link
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to resume_version
ALTER TABLE resume_version
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to ideal_resume
ALTER TABLE ideal_resume
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add updated_at to user_version
ALTER TABLE user_version
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Remove safety_notes from resume_version (no longer used)
ALTER TABLE resume_version
DROP COLUMN IF EXISTS safety_notes;

-- Create index on updated_at for frequently queried tables
CREATE INDEX IF NOT EXISTS ix_resume_raw_updated_at ON resume_raw(updated_at);
CREATE INDEX IF NOT EXISTS ix_vacancy_raw_updated_at ON vacancy_raw(updated_at);
CREATE INDEX IF NOT EXISTS ix_ai_result_updated_at ON ai_result(updated_at);
CREATE INDEX IF NOT EXISTS ix_resume_version_updated_at ON resume_version(updated_at);
