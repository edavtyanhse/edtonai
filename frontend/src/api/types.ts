// API Types - DTOs matching backend schemas

// Common
export interface ApiError {
  detail: string | ValidationError[]
}

export interface ValidationError {
  type: string
  loc: string[]
  msg: string
  input?: unknown
}

// Health & Limits
export interface HealthResponse {
  status: string
  version: string
  database: string
}

export interface LimitsResponse {
  max_resume_chars: number
  max_vacancy_chars: number
}

// ========================================
// Parsed Resume & Vacancy (NEW for Wizard)
// ========================================

export interface PersonalInfo {
  name?: string
  title?: string
  location?: string
  contacts?: Record<string, string>
}

export interface WorkExperience {
  company: string
  title: string
  location?: string
  start_date?: string
  end_date?: string
  is_current?: boolean
  responsibilities?: string[]
  achievements?: string[]
  tech_stack?: string[]
}

export interface Education {
  institution: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

export interface Certification {
  name: string
  issuer?: string
  date?: string
}

export interface Language {
  language: string
  proficiency?: string
}

export interface Skill {
  name: string
  category?: string
  level?: string
}

export interface ParsedResume {
  personal_info?: PersonalInfo
  summary?: string
  skills?: Skill[]
  work_experience?: WorkExperience[]
  education?: Education[]
  certifications?: Certification[]
  languages?: Language[]
  raw_sections?: Record<string, string>
}

export interface ExperienceRequirements {
  min_years?: number
  max_years?: number
  level?: string
  details?: string
}

export interface VacancySkill {
  name: string
  type?: string // hard | soft | domain | tool
  evidence?: string
}

export interface ParsedVacancy {
  job_title?: string
  company?: string
  employment_type?: string
  location?: string
  required_skills?: VacancySkill[]
  preferred_skills?: VacancySkill[]
  experience_requirements?: ExperienceRequirements
  responsibilities?: string[]
  ats_keywords?: string[]
}

// Resume Parse Response
export interface ResumeParseRequest {
  resume_text: string
}

export interface ResumeParseResponse {
  resume_id: string
  resume_hash: string
  parsed_resume: ParsedResume
  cache_hit: boolean
}

export interface ResumeDetailResponse {
  id: string
  source_text: string
  content_hash: string
  parsed_data?: ParsedResume
  created_at: string
  parsed_at?: string
}

// Vacancy Parse Response
export interface VacancyParseRequest {
  vacancy_text: string
  url?: string
}

export interface VacancyParseResponse {
  vacancy_id: string
  vacancy_hash: string
  parsed_vacancy: ParsedVacancy
  cache_hit: boolean
  raw_text: string
}

export interface VacancyDetailResponse {
  id: string
  source_text: string
  content_hash: string
  parsed_data?: ParsedVacancy
  created_at: string
  parsed_at?: string
}

// Patch requests
export interface ResumePatchRequest {
  parsed_data: ParsedResume
}

export interface VacancyPatchRequest {
  parsed_data: ParsedVacancy
}

// ========================================
// Adapt Resume
// ========================================

export interface SelectedImprovement {
  checkbox_id: string
  user_input?: string | null
  ai_generate?: boolean
}

export interface AdaptRequest {
  resume_text?: string
  resume_id?: string
  vacancy_text?: string
  vacancy_id?: string
  selected_improvements?: SelectedImprovement[]
  // Legacy support
  selected_checkbox_ids?: string[]
  base_version_id?: string
  options?: {
    language?: string
    template?: string
  }
}

export interface ChangeLogEntry {
  checkbox_id: string
  what_changed: string
  where: string
  before_excerpt?: string
  after_excerpt?: string
}

export interface AdaptResponse {
  version_id: string
  parent_version_id?: string
  resume_id: string
  vacancy_id: string
  updated_resume_text: string
  change_log: ChangeLogEntry[]
  applied_checkbox_ids: string[]
  cache_hit: boolean
}

// Ideal Resume
export interface IdealRequest {
  vacancy_text?: string
  vacancy_id?: string
  options?: {
    language?: string
    template?: string
    seniority?: string
  }
}

export interface IdealMetadata {
  keywords_used: string[]
  structure: string[]
  assumptions: string[]
  language?: string
  template?: string
}

export interface IdealResponse {
  ideal_id: string
  vacancy_id: string
  ideal_resume_text: string
  metadata: IdealMetadata
  cache_hit: boolean
}

// Match Analysis (for checkbox_options)
export interface MatchRequest {
  resume_text: string
  vacancy_text: string
  // Context for re-analysis after adaptation (optional)
  original_analysis?: MatchAnalysis
  applied_checkbox_ids?: string[]
}

export interface CheckboxOption {
  id: string
  label: string
  description: string
  category: string
  impact: string
  requires_user_input: boolean
  user_input_placeholder: string | null
  // Legacy fields (deprecated)
  priority?: number
  enabled?: boolean
}

export interface Gap {
  id: string
  type: string
  severity: string
  message: string
  suggestion: string
  target_section: string
}

export interface ScoreBreakdown {
  skill_fit?: { value: number; comment: string }
  experience_fit?: { value: number; comment: string }
  ats_fit?: { value: number; comment: string }
  clarity_evidence?: { value: number; comment: string }
}

export interface MatchAnalysis {
  score: number
  score_breakdown: ScoreBreakdown
  matched_required_skills: string[]
  missing_required_skills: string[]
  matched_preferred_skills: string[]
  missing_preferred_skills: string[]
  gaps: Gap[]
  checkbox_options: CheckboxOption[]
}

export interface MatchResponse {
  resume_id: string
  vacancy_id: string
  analysis_id: string
  analysis: MatchAnalysis
  cache_hit: boolean
}

// Versions (History)
export type VersionType = 'adapt' | 'ideal'

export interface VersionCreateRequest {
  type: VersionType
  title?: string
  resume_text: string
  vacancy_text: string
  result_text: string
  change_log?: ChangeLogEntry[]
  selected_checkbox_ids?: string[]
  analysis_id?: string
}

export interface VersionItem {
  id: string
  created_at: string
  type: VersionType
  title?: string
  resume_preview?: string
  vacancy_preview?: string
  result_preview?: string
}

export interface VersionDetail {
  id: string
  created_at: string
  type: VersionType
  title?: string
  resume_text: string
  vacancy_text: string
  result_text: string
  change_log?: ChangeLogEntry[]
  selected_checkbox_ids?: string[]
  analysis_id?: string
}

export interface VersionListResponse {
  items: VersionItem[]
  total: number
}

// ========================================
// Cover Letter Generation
// ========================================

export interface CoverLetterRequest {
  resume_version_id: string
  options?: Record<string, unknown>
}

export interface CoverLetterStructure {
  opening: string
  body: string
  closing: string
}

export interface CoverLetterResponse {
  cover_letter_id: string
  resume_version_id: string
  vacancy_id: string | null
  cover_letter_text: string
  structure: CoverLetterStructure
  key_points_used: string[]
  alignment_notes: string[]
  cache_hit: boolean
}
