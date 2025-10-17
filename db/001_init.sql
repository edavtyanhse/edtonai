create extension if not exists pgcrypto;

create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  title text,
  content text,
  skills text[] default '{}',
  created_at timestamptz default now()
);

create table if not exists vacancies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  source_url text,
  title text,
  description text,
  keywords text[] default '{}',
  created_at timestamptz default now()
);

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  resume_id uuid references resumes(id) on delete cascade,
  vacancy_id uuid references vacancies(id) on delete cascade,
  match_score numeric,
  matched_skills text[] default '{}',
  missing_skills text[] default '{}',
  tips text,
  created_at timestamptz default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  analysis_id uuid references analyses(id) on delete cascade,
  kind text check (kind in ('resume','cover_letter')),
  content text,
  ats_score numeric,
  created_at timestamptz default now()
);