# Frontend Documentation

Техническая документация React SPA для адаптации резюме под вакансию.

## Содержание

| Раздел | Описание |
|--------|----------|
| [Architecture](architecture/) | Архитектура приложения, state management |
| [Components](components/) | UI компоненты и их API |
| [Pages](pages/) | Страницы и wizard flow |
| [API Layer](api/) | HTTP клиент и типы |
| [Context](context/) | React Context для глобального состояния |
| [Styling](styling/) | Tailwind CSS, дизайн-система |

## Стек технологий

- **Runtime:** Node.js 20
- **Framework:** React 18
- **Language:** TypeScript 5
- **Build:** Vite
- **Routing:** React Router v6
- **State Management:** React Context + TanStack Query v5
- **Styling:** Tailwind CSS
- **Auth:** Supabase Auth (Email/Password, Google, etc.)
- **Icons:** Lucide React
- **HTTP Client:** Native Fetch API

## Быстрый старт для разработчика

```bash
cd edtonai/frontend

# Настройка переменных окружения
# Создай .env:
# VITE_SUPABASE_URL=...
# VITE_SUPABASE_ANON_KEY=...

# Установка зависимостей
npm install

# Dev-сервер (порт 5173)
npm run dev
```

### Docker & Deployment

Frontend отдается через **Nginx**. При старте контейнера скрипт `envsubst` подставляет переменную `BACKEND_URL` в конфиг Nginx, чтобы проксирование запросов `/api` шло на правильный бэкенд (локально или в Cloud Run).

```bash
# Локальная сборка
docker build -t edtonai-frontend .
docker run -p 3000:80 \
  -e BACKEND_URL=http://host.docker.internal:8000 \
  edtonai-frontend
```

В **Cloud Run** переменная `BACKEND_URL` должна указывать на URL развернутого бэкенда.

## Структура проекта

```
frontend/
├── src/
│   ├── main.tsx           # Entry point, React root
│   ├── App.tsx            # Router setup, routes
│   ├── index.css          # Global styles, Tailwind imports
│   │
│   ├── api/               # API layer
│   │   ├── client.ts      # HTTP client (fetch wrapper)
│   │   ├── endpoints.ts   # API functions (parseResume, analyzeMatch, etc.)
│   │   ├── types.ts       # TypeScript interfaces matching backend DTOs
│   │   └── index.ts       # Re-exports
│   │
│   ├── components/        # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── CheckboxList.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── CoverLetterModal.tsx
│   │   ├── DiffViewer.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── Layout.tsx
│   │   ├── ResumeEditor.tsx
│   │   ├── TextAreaWithCounter.tsx
│   │   ├── Toast.tsx
│   │   ├── VacancyEditor.tsx
│   │   ├── WizardLayout.tsx
│   │   └── index.ts
│   │
│   ├── context/           # React Context providers
│   │   └── WizardContext.tsx  # Wizard state management
│   │
│   ├── pages/             # Page components
│   │   ├── HomePage.tsx       # Mode selection (wizard vs ideal)
│   │   ├── WizardPage.tsx     # Main wizard container
│   │   ├── IdealResumePage.tsx
│   │   ├── History.tsx
│   │   ├── Compare.tsx
│   │   ├── Workspace.tsx
│   │   ├── index.ts
│   │   │
│   │   └── wizard/        # Wizard step components
│   │       ├── Step1Resume.tsx
│   │       ├── Step2Vacancy.tsx
│   │       ├── Step3Analysis.tsx
│   │       ├── Step4Improvement.tsx
│   │       └── index.ts
│   │
│   └── utils/             # Utility functions
│
├── public/                # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── nginx.conf             # Production nginx config
└── Dockerfile
```

## Архитектура

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        App.tsx (Router)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐    ┌─────────────────────────────────┐    │
│   │   HomePage      │    │   WizardPage                    │    │
│   │   (mode select) │    │   ┌───────────────────────────┐ │    │
│   └─────────────────┘    │   │   WizardProvider          │ │    │
│                          │   │   (WizardContext)         │ │    │
│   ┌─────────────────┐    │   │                           │ │    │
│   │ IdealResumePage │    │   │   ┌───────────────────┐   │ │    │
│   └─────────────────┘    │   │   │  WizardLayout     │   │ │    │
│                          │   │   │  (steps sidebar)  │   │ │    │
│   ┌─────────────────┐    │   │   │                   │   │ │    │
│   │   Layout        │    │   │   │  ┌─────────────┐  │   │ │    │
│   │   (header/nav)  │    │   │   │  │ Step1..4    │  │   │ │    │
│   │   ┌─────────┐   │    │   │   │  │ Components  │  │   │ │    │
│   │   │ History │   │    │   │   │  └─────────────┘  │   │ │    │
│   │   │ Compare │   │    │   │   └───────────────────┘   │ │    │
│   │   └─────────┘   │    │   └───────────────────────────┘ │    │
│   └─────────────────┘    └─────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ TanStack Query
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │  client.ts   │◄───│ endpoints.ts │◄───│  types.ts    │      │
│   │  (fetch)     │    │ (functions)  │    │  (DTOs)      │      │
│   └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP /api/*
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
└─────────────────────────────────────────────────────────────────┘
```

### State Management

```
┌─────────────────────────────────────────────────────────────┐
│                    WizardContext                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  WizardState                                                 │
│  ├── Step 1: resumeText, resumeId, parsedResume             │
│  ├── Step 2: vacancyText, vacancyId, parsedVacancy          │
│  ├── Step 3: analysis, analysisId, previousScore            │
│  └── Step 4: selectedCheckboxes, resultText, changeLog      │
│                                                              │
│  Actions                                                     │
│  ├── setResumeText(), setResumeData(), updateParsedResume() │
│  ├── setVacancyText(), setVacancyData(), updateParsedVacancy│
│  ├── setAnalysis()                                          │
│  ├── setSelectedCheckboxes(), toggleCheckbox(), setResult() │
│  ├── applyImprovedResume()  ← makes improved resume base    │
│  └── canGoToStep(), goToNextStep(), goToPrevStep(), reset() │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### TanStack Query Integration

```typescript
// Mutations для API вызовов
const parseMutation = useMutation({
  mutationFn: () => parseResume({ resume_text: text }),
  onSuccess: (data) => {
    setResumeData(data.resume_id, data.parsed_resume)
  },
})

// Query для загрузки данных
const { data: versions } = useQuery({
  queryKey: ['versions'],
  queryFn: () => getVersions(),
})
```

## Wizard Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        WIZARD FLOW                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │   Step 1    │───►│   Step 2    │───►│   Step 3    │           │
│  │   Resume    │    │   Vacancy   │    │   Analysis  │           │
│  │             │    │             │    │             │           │
│  │ • Input     │    │ • Input     │    │ • Preview   │           │
│  │ • Parse     │    │ • Parse     │    │ • Analyze   │           │
│  │ • Edit      │    │ • Edit      │    │ • Results   │           │
│  └─────────────┘    └─────────────┘    └──────┬──────┘           │
│                                               │                   │
│                                               ▼                   │
│                                        ┌─────────────┐           │
│                                        │   Step 4    │           │
│                                        │ Improvement │           │
│                                        │             │           │
│                                        │ • Checkboxes│           │
│                                        │ • Review    │           │
│                                        │ • Analysis  │◄──┐       │
│                                        └──────┬──────┘   │       │
│                                               │          │       │
│                                               ▼          │       │
│                                        ┌─────────────┐   │       │
│                                        │  Continue?  │───┘       │
│                                        │  Improving  │           │
│                                        └─────────────┘           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Step 1: Resume Input

**Файл:** `pages/wizard/Step1Resume.tsx`

**Режимы:**
- `input` — ввод текста резюме
- `parsed` — редактирование распознанных данных

**Flow:**
1. Пользователь вставляет текст резюме
2. Нажимает "Распознать резюме"
3. API: `POST /v1/resumes/parse`
4. Отображается ResumeEditor для правки
5. Изменения можно сохранить: `PATCH /v1/resumes/{id}`

**Ключевые компоненты:**
- `TextAreaWithCounter` — textarea с лимитом символов
- `ResumeEditor` — форма редактирования parsed данных

### Step 2: Vacancy Input

**Файл:** `pages/wizard/Step2Vacancy.tsx`

Аналогично Step 1, но для вакансии:
- API: `POST /v1/vacancies/parse`
- Компонент: `VacancyEditor`

### Step 3: Analysis

**Файл:** `pages/wizard/Step3Analysis.tsx`

**Flow:**
1. Показывает превью резюме и вакансии
2. Пользователь нажимает "Запустить анализ"
3. API: `POST /v1/match/analyze`
4. Отображается:
   - Общий балл (0-100)
   - Breakdown: skill_fit, experience_fit, ats_fit, clarity
   - Навыки: matched/missing (required + preferred)
   - Gaps с severity (high/medium/low)
   - Checkbox options для улучшений

**Компоненты:**
- `ScoreCard` — карточка с прогресс-баром
- `SkillBadge` — бейдж навыка (matched/missing)

### Step 4: Improvement

**Файл:** `pages/wizard/Step4Improvement.tsx`

**Режимы:**
1. `checkboxes` — выбор улучшений из checkbox_options
2. `review` — подтверждение/отклонение каждого изменения
3. `analysis` — новый анализ после применения улучшений

**Flow:**
```
checkboxes → Apply → review → Confirm → analysis
                                  │
                                  ▼
                        Continue improving?
                                  │
                                  ▼
                            checkboxes (loop)
```

**API вызовы:**
1. `POST /v1/resumes/adapt` — применить улучшения
2. `POST /v1/versions` — сохранить версию
3. `POST /v1/match/analyze` — повторный анализ
4. `POST /v1/cover-letter` — генерация сопроводительного письма

**Ключевая логика:**
- `applyImprovedResume()` — делает улучшенное резюме новым базовым
- `previousScore` — сохраняет старый балл для сравнения
- Score comparison: TrendingUp/TrendingDown icons

## API Layer

### Client (`api/client.ts`)

```typescript
const BASE_URL = '/api'

export const apiClient = {
  async get<T>(path: string, options?: RequestOptions): Promise<T>
  async post<T, D>(path: string, data: D, options?: RequestOptions): Promise<T>
  async patch<T, D>(path: string, data: D, options?: RequestOptions): Promise<T>
  async delete(path: string, options?: RequestOptions): Promise<void>
}
```

**Error handling:**
```typescript
export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown
  ) {}
}
```

### Endpoints (`api/endpoints.ts`)

| Function | Method | Path | Description |
|----------|--------|------|-------------|
| `getHealth()` | GET | `/v1/health` | Health check |
| `getLimits()` | GET | `/v1/limits` | Get text limits |
| `parseResume()` | POST | `/v1/resumes/parse` | Parse resume |
| `getResume()` | GET | `/v1/resumes/{id}` | Get resume |
| `updateResume()` | PATCH | `/v1/resumes/{id}` | Update parsed data |
| `parseVacancy()` | POST | `/v1/vacancies/parse` | Parse vacancy |
| `getVacancy()` | GET | `/v1/vacancies/{id}` | Get vacancy |
| `updateVacancy()` | PATCH | `/v1/vacancies/{id}` | Update parsed data |
| `analyzeMatch()` | POST | `/v1/match/analyze` | Analyze match |
| `adaptResume()` | POST | `/v1/resumes/adapt` | Adapt resume |
| `generateIdeal()` | POST | `/v1/resumes/ideal` | Generate ideal |
| `generateCoverLetter()` | POST | `/v1/cover-letter` | Generate cover letter |
| `createVersion()` | POST | `/v1/versions` | Create version |
| `getVersions()` | GET | `/v1/versions` | List versions |
| `getVersion()` | GET | `/v1/versions/{id}` | Get version |
| `deleteVersion()` | DELETE | `/v1/versions/{id}` | Delete version |

### Types (`api/types.ts`)

Типы соответствуют backend Pydantic схемам:

```typescript
// Core entities
interface ParsedResume { personal_info, summary, skills, work_experience, ... }
interface ParsedVacancy { job_title, required_skills, preferred_skills, ... }
interface MatchAnalysis { score, score_breakdown, gaps, checkbox_options, ... }

// Request/Response
interface ResumeParseRequest { resume_text: string }
interface ResumeParseResponse { resume_id, resume_hash, parsed_resume, cache_hit }

interface AdaptRequest { resume_text?, selected_checkbox_ids, ... }
interface AdaptResponse { version_id, updated_resume_text, change_log, ... }

// Change tracking
interface ChangeLogEntry {
  checkbox_id: string
  what_changed: string
  where: 'summary' | 'skills' | 'experience' | 'education' | 'other'
  before_excerpt?: string
  after_excerpt?: string
}
```

## Components

### Button

```tsx
<Button variant="primary|outline|ghost" size="sm|md|lg" disabled={false}>
  Click me
</Button>
```

### TextAreaWithCounter

```tsx
<TextAreaWithCounter
  value={text}
  onChange={setText}
  maxLength={15000}
  label="Текст резюме"
  placeholder="Вставьте текст..."
  minHeight={400}
/>
```

### CheckboxList

```tsx
<CheckboxList
  options={checkbox_options}  // from analysis
  selected={selectedIds}
  onChange={setSelectedIds}
/>
```

Отображает checkbox_options с:
- enabled/disabled состоянием
- priority (high/medium/low)
- action_hint

### ResumeEditor / VacancyEditor

Формы для редактирования распознанных данных:
- Секции раскрываются/сворачиваются
- Inline редактирование полей
- Добавление/удаление элементов списков

### ConfirmDialog

```tsx
<ConfirmDialog
  isOpen={showDialog}
  title="Подтверждение"
  message="Вы уверены?"
  confirmText="Да"
  onConfirm={handleConfirm}
  onClose={() => setShowDialog(false)}
/>
```

### Toast / Toaster

```tsx
// В App.tsx
<Toaster />

// Использование
import { toast } from '@/components/Toast'
toast.success('Сохранено!')
toast.error('Ошибка!')
```

## Routing

```tsx
// App.tsx
<Routes>
  {/* Home - mode selection */}
  <Route path="/" element={<HomePage />} />
  
  {/* Wizard - main flow */}
  <Route path="/wizard" element={<WizardPage />} />
  
  {/* Ideal resume generator */}
  <Route path="/ideal-resume" element={<IdealResumePage />} />
  
  {/* With Layout (header/nav) */}
  <Route element={<Layout />}>
    <Route path="workspace" element={<Workspace />} />
    <Route path="history" element={<History />} />
    <Route path="compare" element={<Compare />} />
  </Route>
  
  {/* Fallback */}
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

## Styling

### Tailwind Config

```js
// tailwind.config.js
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          // ...
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
}
```

### CSS Classes Pattern

```tsx
// Conditional classes
className={`base-classes ${condition ? 'true-classes' : 'false-classes'}`}

// Score coloring
className={score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'}
```

## Build & Deploy

### Development

```bash
npm run dev
# → http://localhost:5173
# API proxy: /api → http://localhost:8000
```

### Production

```bash
npm run build
# → dist/

# Docker
docker build -t edtonai-frontend .
```

### Nginx Config

```nginx
# nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://backend:8000/;
    }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api` | API base URL (for dev) |

## Error Handling

1. **API errors** — отображаются в UI как alert/toast
2. **Validation errors** — подсвечиваются в формах
3. **ErrorBoundary** — ловит React ошибки

```tsx
// components/ErrorBoundary.tsx
class ErrorBoundary extends Component {
  componentDidCatch(error, errorInfo) {
    // Log to console or error tracking service
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback onReset={() => this.setState({ hasError: false })} />
    }
    return this.props.children
  }
}
```
