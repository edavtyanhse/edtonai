-- Script to clear all data from the database
-- Run this after applying migrations to start fresh

-- Disable foreign key checks temporarily
-- Note: In PostgreSQL we need to truncate with CASCADE

-- Clear all tables in correct order (respecting foreign keys)
TRUNCATE TABLE 
    user_version,
    resume_version,
    ideal_resume,
    analysis_link,
    ai_result,
    vacancy_raw,
    resume_raw
CASCADE;

-- Reset sequences if needed
-- (PostgreSQL UUIDs don't use sequences, so this is just for any auto-increment IDs)

-- Confirm
SELECT 'Database cleared successfully' as status;
