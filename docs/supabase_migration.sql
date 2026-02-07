-- SQL Migration for EdTon.ai: Add user_id to user_version table and enable RLS
-- Run this in Supabase Dashboard -> SQL Editor

-- =====================================================
-- 1. Add user_id column to user_version table
-- =====================================================
ALTER TABLE public.user_version 
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Create index for faster lookups by user_id
CREATE INDEX IF NOT EXISTS idx_user_version_user_id ON public.user_version(user_id);

-- =====================================================
-- 2. Update existing records with a specific user_id
-- Replace 'YOUR_USER_ID_HERE' with your actual Supabase user ID
-- You can find it in Authentication -> Users section
-- =====================================================
UPDATE public.user_version 
SET user_id = 'YOUR_USER_ID_HERE' 
WHERE user_id IS NULL;

-- =====================================================
-- 3. Enable Row Level Security (RLS) on all tables
-- =====================================================

-- Enable RLS on user_version
ALTER TABLE public.user_version ENABLE ROW LEVEL SECURITY;

-- Enable RLS on other tables
ALTER TABLE public.resume_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vacancy_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_result ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ideal_resume ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. Create RLS policies for user_version
-- =====================================================

-- Policy: Users can only see their own versions
CREATE POLICY "Users can view own versions"
ON public.user_version
FOR SELECT
USING (user_id = auth.uid()::text OR user_id IS NULL);

-- Policy: Users can insert versions with their user_id
CREATE POLICY "Users can insert own versions"
ON public.user_version
FOR INSERT
WITH CHECK (user_id = auth.uid()::text OR user_id IS NULL);

-- Policy: Users can update their own versions
CREATE POLICY "Users can update own versions"
ON public.user_version
FOR UPDATE
USING (user_id = auth.uid()::text);

-- Policy: Users can delete their own versions
CREATE POLICY "Users can delete own versions"
ON public.user_version
FOR DELETE
USING (user_id = auth.uid()::text);

-- =====================================================
-- 5. Create basic RLS policies for other tables
-- These allow authenticated users full access
-- You may want to refine these later
-- =====================================================

-- resume_raw
CREATE POLICY "Authenticated users can access resume_raw"
ON public.resume_raw
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- vacancy_raw
CREATE POLICY "Authenticated users can access vacancy_raw"
ON public.vacancy_raw
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- analysis_link
CREATE POLICY "Authenticated users can access analysis_link"
ON public.analysis_link
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- ai_result
CREATE POLICY "Authenticated users can access ai_result"
ON public.ai_result
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- resume_version
CREATE POLICY "Authenticated users can access resume_version"
ON public.resume_version
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- ideal_resume
CREATE POLICY "Authenticated users can access ideal_resume"
ON public.ideal_resume
FOR ALL
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- =====================================================
-- 6. Enable Leaked Password Protection (from Security Advisor warning)
-- Go to Authentication -> Settings -> Security and enable it there
-- =====================================================
