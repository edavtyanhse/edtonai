-- Migration: Extend feedback table for CSAT/NPS and experiment context
-- Safe to run multiple times.

ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS metric_type VARCHAR(16);

ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS score INTEGER;

ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS context_step VARCHAR(64);

ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS ui_variant VARCHAR(16);

ALTER TABLE feedback
    ADD COLUMN IF NOT EXISTS user_segment VARCHAR(64);

UPDATE feedback
SET metric_type = COALESCE(metric_type, 'csat'),
    score = COALESCE(score, 5)
WHERE metric_type IS NULL
   OR score IS NULL;

ALTER TABLE feedback
    ALTER COLUMN metric_type SET NOT NULL;

ALTER TABLE feedback
    ALTER COLUMN score SET NOT NULL;

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

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_feedback_score_by_metric'
    ) THEN
        ALTER TABLE feedback
            ADD CONSTRAINT ck_feedback_score_by_metric
            CHECK (
                (metric_type = 'csat' AND score BETWEEN 1 AND 5)
                OR (metric_type = 'nps' AND score BETWEEN 0 AND 10)
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_feedback_metric_type ON feedback(metric_type);
CREATE INDEX IF NOT EXISTS idx_feedback_context_step ON feedback(context_step);
CREATE INDEX IF NOT EXISTS idx_feedback_ui_variant ON feedback(ui_variant);
CREATE INDEX IF NOT EXISTS idx_feedback_user_segment ON feedback(user_segment);
