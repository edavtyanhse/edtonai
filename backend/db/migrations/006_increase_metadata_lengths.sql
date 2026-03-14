-- Migration: Increase metadata column lengths (Stage 2)
-- Tables: ai_result, resume_version

DO $$ 
BEGIN
    -- ai_result: operation (50 -> 100)
    ALTER TABLE ai_result ALTER COLUMN operation TYPE VARCHAR(100);
    
    -- ai_result: provider (50 -> 100)
    ALTER TABLE ai_result ALTER COLUMN provider TYPE VARCHAR(100);
    
    -- ai_result: model (100 -> 255)
    ALTER TABLE ai_result ALTER COLUMN model TYPE VARCHAR(255);
    
    -- resume_version: provider (50 -> 100)
    ALTER TABLE resume_version ALTER COLUMN provider TYPE VARCHAR(100);
    
    -- resume_version: model (100 -> 255)
    ALTER TABLE resume_version ALTER COLUMN model TYPE VARCHAR(255);
END $$;
