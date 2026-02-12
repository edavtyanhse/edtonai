-- Migration: Add source_url column to vacancy_raw table
-- Stores the URL the vacancy was fetched from (e.g. HH.ru link)

ALTER TABLE vacancy_raw
ADD COLUMN IF NOT EXISTS source_url VARCHAR(2048) DEFAULT NULL;

COMMENT ON COLUMN vacancy_raw.source_url IS 'URL the vacancy was fetched from (hh.ru, etc.)';
