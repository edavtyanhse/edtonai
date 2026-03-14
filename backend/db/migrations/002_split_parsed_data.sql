-- Migration: Split parsed_data into separate columns
-- Resume table

-- Add new columns (if they don't exist)
DO $$ 
BEGIN
    -- personal_info
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='personal_info') THEN
        ALTER TABLE resume_raw ADD COLUMN personal_info JSONB;
    END IF;
    
    -- summary
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='summary') THEN
        ALTER TABLE resume_raw ADD COLUMN summary TEXT;
    END IF;
    
    -- skills
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='skills') THEN
        ALTER TABLE resume_raw ADD COLUMN skills JSONB DEFAULT '[]';
    END IF;
    
    -- work_experience
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='work_experience') THEN
        ALTER TABLE resume_raw ADD COLUMN work_experience JSONB DEFAULT '[]';
    END IF;
    
    -- education
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='education') THEN
        ALTER TABLE resume_raw ADD COLUMN education JSONB DEFAULT '[]';
    END IF;
    
    -- certifications
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='certifications') THEN
        ALTER TABLE resume_raw ADD COLUMN certifications JSONB DEFAULT '[]';
    END IF;
    
    -- languages
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='languages') THEN
        ALTER TABLE resume_raw ADD COLUMN languages JSONB DEFAULT '[]';
    END IF;
    
    -- raw_sections
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_raw' AND column_name='raw_sections') THEN
        ALTER TABLE resume_raw ADD COLUMN raw_sections JSONB DEFAULT '{}';
    END IF;
END $$;

-- Migrate data from parsed_data to new columns (if parsed_data exists)
UPDATE resume_raw SET 
    personal_info = COALESCE(parsed_data->'personal_info', personal_info),
    summary = COALESCE(parsed_data->>'summary', summary),
    skills = COALESCE(parsed_data->'skills', skills, '[]'),
    work_experience = COALESCE(parsed_data->'work_experience', work_experience, '[]'),
    education = COALESCE(parsed_data->'education', education, '[]'),
    certifications = COALESCE(parsed_data->'certifications', certifications, '[]'),
    languages = COALESCE(parsed_data->'languages', languages, '[]'),
    raw_sections = COALESCE(parsed_data->'raw_sections', raw_sections, '{}')
WHERE parsed_data IS NOT NULL 
  AND (personal_info IS NULL OR skills IS NULL OR skills = '[]');

-- Drop old parsed_data column (optional - uncomment if you want to remove it)
-- ALTER TABLE resume_raw DROP COLUMN IF EXISTS parsed_data;

-- Vacancy table

DO $$ 
BEGIN
    -- job_title
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='job_title') THEN
        ALTER TABLE vacancy_raw ADD COLUMN job_title VARCHAR(255);
    END IF;
    
    -- company
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='company') THEN
        ALTER TABLE vacancy_raw ADD COLUMN company VARCHAR(255);
    END IF;
    
    -- employment_type
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='employment_type') THEN
        ALTER TABLE vacancy_raw ADD COLUMN employment_type VARCHAR(100);
    END IF;
    
    -- location
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='location') THEN
        ALTER TABLE vacancy_raw ADD COLUMN location VARCHAR(255);
    END IF;
    
    -- required_skills
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='required_skills') THEN
        ALTER TABLE vacancy_raw ADD COLUMN required_skills JSONB DEFAULT '[]';
    END IF;
    
    -- preferred_skills
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='preferred_skills') THEN
        ALTER TABLE vacancy_raw ADD COLUMN preferred_skills JSONB DEFAULT '[]';
    END IF;
    
    -- experience_requirements
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='experience_requirements') THEN
        ALTER TABLE vacancy_raw ADD COLUMN experience_requirements JSONB;
    END IF;
    
    -- responsibilities
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='responsibilities') THEN
        ALTER TABLE vacancy_raw ADD COLUMN responsibilities JSONB DEFAULT '[]';
    END IF;
    
    -- ats_keywords
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vacancy_raw' AND column_name='ats_keywords') THEN
        ALTER TABLE vacancy_raw ADD COLUMN ats_keywords JSONB DEFAULT '[]';
    END IF;
END $$;

-- Migrate data from parsed_data to new columns (if parsed_data exists)
UPDATE vacancy_raw SET 
    job_title = COALESCE(parsed_data->>'job_title', job_title),
    company = COALESCE(parsed_data->>'company', company),
    employment_type = COALESCE(parsed_data->>'employment_type', employment_type),
    location = COALESCE(parsed_data->>'location', location),
    required_skills = COALESCE(parsed_data->'required_skills', required_skills, '[]'),
    preferred_skills = COALESCE(parsed_data->'preferred_skills', preferred_skills, '[]'),
    experience_requirements = COALESCE(parsed_data->'experience_requirements', experience_requirements),
    responsibilities = COALESCE(parsed_data->'responsibilities', responsibilities, '[]'),
    ats_keywords = COALESCE(parsed_data->'ats_keywords', ats_keywords, '[]')
WHERE parsed_data IS NOT NULL 
  AND (job_title IS NULL OR required_skills IS NULL OR required_skills = '[]');

-- Drop old parsed_data column (optional - uncomment if you want to remove it)
-- ALTER TABLE vacancy_raw DROP COLUMN IF EXISTS parsed_data;
