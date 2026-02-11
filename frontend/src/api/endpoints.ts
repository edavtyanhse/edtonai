import { apiClient } from './client'
import type {
  HealthResponse,
  LimitsResponse,
  AdaptRequest,
  AdaptResponse,
  IdealRequest,
  IdealResponse,
  CoverLetterRequest,
  CoverLetterResponse,
  MatchRequest,
  MatchResponse,
  VersionCreateRequest,
  VersionDetail,
  VersionListResponse,
  ResumeParseRequest,
  ResumeParseResponse,
  ResumeDetailResponse,
  ResumePatchRequest,
  VacancyParseRequest,
  VacancyParseResponse,
  VacancyDetailResponse,
  VacancyPatchRequest,
} from './types'

// Health & Limits
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>('/v1/health', { signal })
}

export async function getLimits(signal?: AbortSignal): Promise<LimitsResponse> {
  return apiClient.get<LimitsResponse>('/v1/limits', { signal })
}

// ========================================
// Resume Parsing & Editing (NEW)
// ========================================

export async function parseResume(
  data: ResumeParseRequest,
  signal?: AbortSignal
): Promise<ResumeParseResponse> {
  return apiClient.post<ResumeParseResponse>('/v1/resumes/parse', data, { signal })
}

export async function getResume(
  resumeId: string,
  signal?: AbortSignal
): Promise<ResumeDetailResponse> {
  return apiClient.get<ResumeDetailResponse>(`/v1/resumes/${resumeId}`, { signal })
}

export async function updateResume(
  resumeId: string,
  data: ResumePatchRequest,
  signal?: AbortSignal
): Promise<ResumeDetailResponse> {
  return apiClient.patch<ResumeDetailResponse>(`/v1/resumes/${resumeId}`, data, { signal })
}

// ========================================
// Vacancy Parsing & Editing (NEW)
// ========================================

export async function parseVacancy(
  data: VacancyParseRequest,
  signal?: AbortSignal
): Promise<VacancyParseResponse> {
  return apiClient.post<VacancyParseResponse>('/v1/vacancies/parse', data, { signal })
}

export async function getVacancy(
  vacancyId: string,
  signal?: AbortSignal
): Promise<VacancyDetailResponse> {
  return apiClient.get<VacancyDetailResponse>(`/v1/vacancies/${vacancyId}`, { signal })
}

export async function updateVacancy(
  vacancyId: string,
  data: VacancyPatchRequest,
  signal?: AbortSignal
): Promise<VacancyDetailResponse> {
  return apiClient.patch<VacancyDetailResponse>(`/v1/vacancies/${vacancyId}`, data, { signal })
}

// ========================================
// Match Analysis
// ========================================

export async function analyzeMatch(
  data: MatchRequest,
  signal?: AbortSignal
): Promise<MatchResponse> {
  return apiClient.post<MatchResponse>('/v1/match/analyze', data, { signal })
}

// Adapt Resume
export async function adaptResume(
  data: AdaptRequest,
  signal?: AbortSignal
): Promise<AdaptResponse> {
  return apiClient.post<AdaptResponse>('/v1/resumes/adapt', data, { signal })
}

// Ideal Resume
export async function generateIdeal(
  data: IdealRequest,
  signal?: AbortSignal
): Promise<IdealResponse> {
  return apiClient.post<IdealResponse>('/v1/resumes/ideal', data, { signal })
}

// Cover Letter
export async function generateCoverLetter(
  data: CoverLetterRequest,
  signal?: AbortSignal
): Promise<CoverLetterResponse> {
  return apiClient.post<CoverLetterResponse>('/v1/cover-letter', data, { signal })
}

// Versions CRUD
export async function createVersion(
  data: VersionCreateRequest,
  signal?: AbortSignal
): Promise<{ id: string; created_at: string }> {
  return apiClient.post('/v1/versions', data, { signal })
}

export async function getVersions(
  limit = 50,
  offset = 0,
  signal?: AbortSignal
): Promise<VersionListResponse> {
  return apiClient.get<VersionListResponse>(`/v1/versions?limit=${limit}&offset=${offset}`, {
    signal,
  })
}

export async function getVersion(id: string, signal?: AbortSignal): Promise<VersionDetail> {
  return apiClient.get<VersionDetail>(`/v1/versions/${id}`, { signal })
}

export async function deleteVersion(
  id: string,
  signal?: AbortSignal
): Promise<void> {
  return apiClient.delete(`/v1/versions/${id}`, { signal })
}
