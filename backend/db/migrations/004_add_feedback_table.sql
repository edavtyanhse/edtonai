-- Migration: Create feedback table
-- To enable: Set FEEDBACK_COLLECTION_ENABLED=true in config
-- To remove: DROP TABLE feedback;

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR NOT NULL,
    feedback_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_email ON feedback(user_email);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
