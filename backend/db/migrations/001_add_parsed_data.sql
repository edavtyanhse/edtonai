-- Migration: Add parsed_data and parsed_at columns to resume_raw and vacancy_raw tables
-- Run this if tables already exist and you don't want to lose data

-- For resume_raw
ALTER TABLE resume_raw
ADD COLUMN IF NOT EXISTS parsed_data JSONB,
ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP;

-- For vacancy_raw
ALTER TABLE vacancy_raw
ADD COLUMN IF NOT EXISTS parsed_data JSONB,
ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP;
