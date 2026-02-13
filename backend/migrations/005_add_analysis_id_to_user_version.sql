-- Add analysis_id to user_version table
ALTER TABLE user_version
ADD COLUMN analysis_id UUID;

-- Add foreign key constraint (optional but recommended for integrity)
ALTER TABLE user_version
ADD CONSTRAINT fk_user_version_analysis
FOREIGN KEY (analysis_id)
REFERENCES ai_result(id)
ON DELETE SET NULL;

-- Create index for performance
CREATE INDEX ix_user_version_analysis_id ON user_version(analysis_id);
