# API Layer

HTTP клиент и типы для взаимодействия с backend.

## Файлы

```
frontend/src/api/
├── client.ts      # HTTP клиент (fetch wrapper)
├── endpoints.ts   # API функции
├── types.ts       # TypeScript типы
└── index.ts       # Re-exports
```

## Client (`client.ts`)

### ApiClient

Обёртка над `fetch` с обработкой ошибок и типизацией.

```typescript
const BASE_URL = '/api'

export const apiClient = {
  async get<T>(path: string, options?: RequestOptions): Promise<T>,
  async post<T, D>(path: string, data: D, options?: RequestOptions): Promise<T>,
  async patch<T, D>(path: string, data: D, options?: RequestOptions): Promise<T>,
  async delete(path: string, options?: RequestOptions): Promise<void>,
}
```

### RequestOptions

```typescript
interface RequestOptions {
  signal?: AbortSignal  // Для отмены запроса
}
```

### Error Handling

```typescript
export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,      // HTTP status code
    public detail?: unknown     // Backend error detail
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}
```

**Логика обработки:**
1. Если `response.ok === false`, парсим body как JSON
2. Извлекаем `detail` (строка или массив ValidationError)
3. Формируем human-readable message
4. Бросаем `ApiClientError`

```typescript
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: unknown
    try {
      const errorBody = await response.json()
      detail = errorBody.detail
    } catch {
      detail = response.statusText
    }

    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((e) => e.msg).join(', ')
          : `Request failed: ${response.status}`

    throw new ApiClientError(message, response.status, detail)
  }

  return response.json()
}
```

## Endpoints (`endpoints.ts`)

### Health & Limits

```typescript
// Health check
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse>

// Get text limits
export async function getLimits(signal?: AbortSignal): Promise<LimitsResponse>
```

### Resume Operations

```typescript
// Parse resume text
export async function parseResume(
  data: ResumeParseRequest,
  signal?: AbortSignal
): Promise<ResumeParseResponse>

// Get resume by ID
export async function getResume(
  resumeId: string,
  signal?: AbortSignal
): Promise<ResumeDetailResponse>

// Update parsed data
export async function updateResume(
  resumeId: string,
  data: ResumePatchRequest,
  signal?: AbortSignal
): Promise<ResumeDetailResponse>
```

### Vacancy Operations

```typescript
// Parse vacancy text
export async function parseVacancy(
  data: VacancyParseRequest,
  signal?: AbortSignal
): Promise<VacancyParseResponse>

// Get vacancy by ID
export async function getVacancy(
  vacancyId: string,
  signal?: AbortSignal
): Promise<VacancyDetailResponse>

// Update parsed data
export async function updateVacancy(
  vacancyId: string,
  data: VacancyPatchRequest,
  signal?: AbortSignal
): Promise<VacancyDetailResponse>
```

### Match Analysis

```typescript
// Analyze resume-vacancy match
export async function analyzeMatch(
  data: MatchRequest,
  signal?: AbortSignal
): Promise<MatchResponse>
```

### Adapt Resume

```typescript
// Apply improvements to resume
export async function adaptResume(
  data: AdaptRequest,
  signal?: AbortSignal
): Promise<AdaptResponse>
```

### Ideal Resume

```typescript
// Generate ideal resume for vacancy
export async function generateIdeal(
  data: IdealRequest,
  signal?: AbortSignal
): Promise<IdealResponse>
```

### Versions CRUD

```typescript
// Create version
export async function createVersion(
  data: VersionCreateRequest,
  signal?: AbortSignal
): Promise<{ id: string; created_at: string }>

// List versions
export async function getVersions(
  limit?: number,
  offset?: number,
  signal?: AbortSignal
): Promise<VersionListResponse>

// Get version by ID
export async function getVersion(
  id: string,
  signal?: AbortSignal
): Promise<VersionDetail>

// Delete version
export async function deleteVersion(
  id: string,
  signal?: AbortSignal
): Promise<void>
```

## Types (`types.ts`)

### Common Types

```typescript
export interface ApiError {
  detail: string | ValidationError[]
}

export interface ValidationError {
  type: string
  loc: string[]
  msg: string
  input?: unknown
}

export interface HealthResponse {
  status: string
  version: string
  database: string
}

export interface LimitsResponse {
  max_resume_chars: number
  max_vacancy_chars: number
}
```

### Parsed Resume

```typescript
export interface PersonalInfo {
  name?: string
  title?: string
  location?: string
  contacts?: Record<string, string>
}

export interface Skill {
  name: string
  category?: string  // language | framework | database | cloud | devops | tool | soft
  level?: string     // junior | middle | senior | unknown
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
```

### Parsed Vacancy

```typescript
export interface VacancySkill {
  name: string
  type?: string      // hard | soft | domain | tool
  evidence?: string  // Quote from vacancy
}

export interface ExperienceRequirements {
  min_years?: number
  max_years?: number
  level?: string
  details?: string
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
```

### Match Analysis

```typescript
export interface ScoreBreakdownItem {
  value: number
  comment: string
}

export interface ScoreBreakdown {
  skill_fit?: ScoreBreakdownItem
  experience_fit?: ScoreBreakdownItem
  ats_fit?: ScoreBreakdownItem
  clarity_evidence?: ScoreBreakdownItem
}

export interface Gap {
  id: string
  type: 'missing_skill' | 'experience_gap' | 'ats_keyword' | 'weak_evidence' | 'weak_wording'
  severity: 'low' | 'medium' | 'high'
  message: string
  suggestion?: string
  target_section: 'summary' | 'skills' | 'experience' | 'education' | 'other'
}

export interface CheckboxOption {
  id: string
  label: string
  impact: 'low' | 'medium' | 'high'
  action_hint: string
  enabled: boolean
  priority: number  // 1-3, higher = more important
}

export interface MatchAnalysis {
  score: number
  score_breakdown: ScoreBreakdown
  matched_required_skills: string[]
  missing_required_skills: string[]
  matched_preferred_skills: string[]
  missing_preferred_skills: string[]
  ats: {
    covered_keywords: string[]
    missing_keywords: string[]
    coverage_ratio: number
  }
  gaps: Gap[]
  checkbox_options: CheckboxOption[]
}
```

### Adapt Types

```typescript
export interface AdaptRequest {
  resume_text?: string
  resume_id?: string
  vacancy_text?: string
  vacancy_id?: string
  selected_checkbox_ids: string[]
  base_version_id?: string
  options?: {
    language?: string
    template?: string
  }
}

export interface ChangeLogEntry {
  checkbox_id: string
  what_changed: string
  where: 'summary' | 'skills' | 'experience' | 'education' | 'other'
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
  safety_notes: string[]
  cache_hit: boolean
}
```

### Version Types

```typescript
export interface VersionCreateRequest {
  type: 'adapt' | 'ideal' | 'manual'
  title?: string
  resume_text?: string
  vacancy_text?: string
  result_text: string
  selected_checkbox_ids?: string[]
}

export interface VersionDetail {
  id: string
  type: string
  title?: string
  resume_text?: string
  vacancy_text?: string
  result_text: string
  created_at: string
  // ...
}

export interface VersionListResponse {
  items: VersionDetail[]
  total: number
}
```

## Usage with TanStack Query

### Mutations

```tsx
import { useMutation } from '@tanstack/react-query'
import { parseResume, adaptResume } from '@/api'

// Parse mutation
const parseMutation = useMutation({
  mutationFn: () => parseResume({ resume_text: text }),
  onSuccess: (data) => {
    setResumeData(data.resume_id, data.parsed_resume)
  },
  onError: (error) => {
    toast.error(error.message)
  },
})

// Usage
parseMutation.mutate()
parseMutation.isPending  // Loading state
parseMutation.isError    // Error state
parseMutation.error      // Error object
```

### Queries

```tsx
import { useQuery } from '@tanstack/react-query'
import { getVersions } from '@/api'

const { data, isLoading, error } = useQuery({
  queryKey: ['versions'],
  queryFn: () => getVersions(50, 0),
})
```

### Abort Controller

```tsx
// Automatic abort on unmount
const { data } = useQuery({
  queryKey: ['resume', resumeId],
  queryFn: ({ signal }) => getResume(resumeId, signal),
})

// Manual abort
const abortController = new AbortController()
await parseResume({ resume_text: text }, abortController.signal)
abortController.abort()
```

## Proxy Configuration

### Development (Vite)

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

### Production (Nginx)

```nginx
location /api/ {
    proxy_pass http://backend:8000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```
