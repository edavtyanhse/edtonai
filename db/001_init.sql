create extension if not exists pgcrypto;

create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text,
  content text not null,
  skills jsonb default '[]'::jsonb,
  created_at timestamptz default now()
);

create table if not exists vacancies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  source_url text,
  title text,
  description text not null,
  keywords jsonb default '[]'::jsonb,
  created_at timestamptz default now()
);

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  resume_id uuid references resumes(id) on delete cascade,
  vacancy_id uuid references vacancies(id) on delete cascade,
  role text,
  match_score numeric,
  matched_skills jsonb default '[]'::jsonb,
  missing_skills jsonb default '[]'::jsonb,
  tips text,
  created_at timestamptz default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  analysis_id uuid references analyses(id) on delete cascade,
  kind text check (kind in ('resume','cover_letter')),
  content text not null,
  ats_score numeric,
  created_at timestamptz default now()
);