# Architecture

Архитектура frontend приложения.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Browser                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    React Application                     │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              Routing (React Router)              │    │    │
│  │  │                                                  │    │    │
│  │  │    /          → HomePage                         │    │    │
│  │  │    /wizard    → WizardPage                       │    │    │
│  │  │    /ideal     → IdealResumePage                  │    │    │
│  │  │    /history   → History                          │    │    │
│  │  │    /compare   → Compare                          │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                          │                               │    │
│  │  ┌───────────────────────┼───────────────────────────┐  │    │
│  │  │     State Management  │                            │  │    │
│  │  │                       │                            │  │    │
│  │  │  ┌────────────────────┴────────────────────────┐  │  │    │
│  │  │  │           WizardContext (React Context)     │  │  │    │
│  │  │  │  • resumeText, parsedResume                 │  │  │    │
│  │  │  │  • vacancyText, parsedVacancy               │  │  │    │
│  │  │  │  • analysis, selectedCheckboxes             │  │  │    │
│  │  │  │  • resultText, changeLog                    │  │  │    │
│  │  │  └─────────────────────────────────────────────┘  │  │    │
│  │  │                       │                            │  │    │
│  │  │  ┌────────────────────┴────────────────────────┐  │  │    │
│  │  │  │          TanStack Query (Server State)      │  │  │    │
│  │  │  │  • Mutations (parse, analyze, adapt)        │  │  │    │
│  │  │  │  • Queries (versions, health)               │  │  │    │
│  │  │  │  • Cache management                         │  │  │    │
│  │  │  └─────────────────────────────────────────────┘  │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  │                          │                               │    │
│  │  ┌───────────────────────┼───────────────────────────┐  │    │
│  │  │            API Layer  │                            │  │    │
│  │  │                       │                            │  │    │
│  │  │  ┌────────────────────┴────────────────────────┐  │  │    │
│  │  │  │              apiClient (fetch)              │  │  │    │
│  │  │  │  • get, post, patch, delete                 │  │  │    │
│  │  │  │  • Error handling                           │  │  │    │
│  │  │  │  • Type safety                              │  │  │    │
│  │  │  └─────────────────────────────────────────────┘  │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  │                          │                               │    │
│  └──────────────────────────┼───────────────────────────────┘    │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │ HTTP /api/*
                              │
┌─────────────────────────────┼─────────────────────────────────────┐
│                    Nginx (proxy)                                  │
│                             │                                     │
│    /api/* ──────────────────┼──────────────────► Backend:8000    │
│    /* ──────────────────────┼──────────────────► Static files    │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────────────┐
│                    Backend (FastAPI)                              │
└───────────────────────────────────────────────────────────────────┘
```

## Layered Architecture

### 1. Presentation Layer (Pages & Components)

**Назначение:** UI отображение и взаимодействие с пользователем.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pages (routes)              Components (reusable UI)            │
│  ├── HomePage               ├── Button                          │
│  ├── WizardPage             ├── TextAreaWithCounter              │
│  │   ├── Step1Resume        ├── CheckboxList                     │
│  │   ├── Step2Vacancy       ├── ResumeEditor                     │
│  │   ├── Step3Analysis      ├── VacancyEditor                    │
│  │   └── Step4Improvement   ├── ConfirmDialog                    │
│  ├── IdealResumePage        ├── DiffViewer                       │
│  ├── History                ├── Layout                           │
│  └── Compare                └── WizardLayout                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Принципы:**
- Pages отвечают за бизнес-логику конкретного экрана
- Components — переиспользуемые UI блоки без бизнес-логики
- Используют hooks для доступа к state и API

### 2. State Management Layer

**Назначение:** Управление состоянием приложения.

```
┌─────────────────────────────────────────────────────────────────┐
│                    State Management Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WizardContext (client state)      TanStack Query (server state) │
│  ├── resumeText                   ├── Mutations                  │
│  ├── parsedResume                 │   ├── parseResumeMutation    │
│  ├── vacancyText                  │   ├── parseVacancyMutation   │
│  ├── parsedVacancy                │   ├── analyzeMutation        │
│  ├── analysis                     │   ├── adaptMutation          │
│  ├── selectedCheckboxes           │   └── saveMutation           │
│  ├── resultText                   │                              │
│  └── changeLog                    ├── Queries                    │
│                                   │   ├── versionsQuery          │
│  Actions:                         │   └── healthQuery            │
│  ├── setResumeText()              │                              │
│  ├── setAnalysis()                └── Cache                      │
│  ├── setSelectedCheckboxes()          ├── queryKey management    │
│  ├── applyImprovedResume()            └── stale time config      │
│  └── reset()                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Разделение ответственности:**
- **WizardContext** — клиентское состояние wizard flow (текущий шаг, введённые данные, выбранные опции)
- **TanStack Query** — серверное состояние (кеш ответов API, loading/error states)

### 3. API Layer

**Назначение:** Взаимодействие с backend.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  types.ts          endpoints.ts       client.ts                  │
│  ├── ParsedResume  ├── parseResume()  ├── apiClient.get()        │
│  ├── ParsedVacancy ├── parseVacancy() ├── apiClient.post()       │
│  ├── MatchAnalysis ├── analyzeMatch() ├── apiClient.patch()      │
│  ├── AdaptResponse ├── adaptResume()  ├── apiClient.delete()     │
│  └── ...           ├── getVersions()  │                          │
│                    └── ...            └── ApiClientError         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Принципы:**
- Типы соответствуют backend Pydantic схемам
- Endpoints — чистые функции без side effects
- Client инкапсулирует fetch + error handling

## Data Flow

### Wizard Flow

```
User Input → Component → Context Action → API Mutation → Backend
                                              ↓
                                        onSuccess
                                              ↓
User Display ← Component ← Context State ← Update State
```

### Пример: Парсинг резюме

```
Step1Resume                    WizardContext              API
     │                              │                      │
     │ localText = "..."            │                      │
     │                              │                      │
     │ [Click: Распознать]          │                      │
     │                              │                      │
     ├──────── parseMutation.mutate() ─────────────────────┤
     │                              │                      │
     │                              │     POST /parse      │
     │                              │ ──────────────────► │
     │                              │                      │
     │                              │ ◄─── response ────── │
     │                              │                      │
     │ ◄───── onSuccess ───────────┤                      │
     │                              │                      │
     │ setResumeText(localText)     │                      │
     │ setResumeData(id, parsed)    │                      │
     │                              │                      │
     │ setMode('parsed')            │                      │
     │                              │                      │
     │ [Render ResumeEditor]        │                      │
     │                              │                      │
```

## Component Hierarchy

```
App
├── HomePage
│
├── WizardPage
│   └── WizardProvider (context)
│       └── WizardLayout
│           ├── StepsSidebar
│           │   ├── StepItem (1-4)
│           │   └── StepItem
│           │
│           └── StepContent
│               ├── Step1Resume
│               │   ├── TextAreaWithCounter
│               │   ├── Button
│               │   └── ResumeEditor
│               │
│               ├── Step2Vacancy
│               │   ├── TextAreaWithCounter
│               │   ├── Button
│               │   └── VacancyEditor
│               │
│               ├── Step3Analysis
│               │   ├── ScoreCard (x4)
│               │   ├── SkillBadge (many)
│               │   └── GapCard (many)
│               │
│               └── Step4Improvement
│                   ├── CheckboxList
│                   ├── ChangeReviewCard (many)
│                   ├── ScoreCard (x4)
│                   └── ConfirmDialog
│
├── IdealResumePage
│   ├── TextAreaWithCounter
│   └── Button
│
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   └── Navigation
│   │
│   └── Outlet
│       ├── History
│       │   └── VersionTable
│       │
│       └── Compare
│           ├── VersionSelector (x2)
│           └── DiffViewer
│
└── Toaster (global)
```

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Boundaries                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ErrorBoundary (root)                                            │
│  └── Catches uncaught React errors                               │
│      └── Shows fallback UI with reset option                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    API Error Handling                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  apiClient                                                       │
│  └── Throws ApiClientError with status, message, detail          │
│                                                                  │
│  TanStack Query mutations                                        │
│  └── onError callback                                            │
│      └── toast.error(error.message)                              │
│                                                                  │
│  Components                                                      │
│  └── mutation.isError && <ErrorAlert>{error.message}</ErrorAlert>│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Considerations

### Code Splitting

- Lazy loading страниц (пока не реализовано)
- Можно добавить `React.lazy()` для крупных страниц

### Memoization

```tsx
// Context actions memoized with useCallback
const setResumeText = useCallback((text: string) => {
  setState((prev) => ({ ...prev, resumeText: text }))
}, [])

// Components can use React.memo for expensive renders
export const ExpensiveComponent = React.memo(function ExpensiveComponent(props) {
  // ...
})
```

### TanStack Query Caching

```tsx
// Queries are cached by queryKey
const { data } = useQuery({
  queryKey: ['versions'],
  queryFn: getVersions,
  staleTime: 5 * 60 * 1000, // 5 minutes
})
```

## Testing Strategy (TODO)

### Unit Tests
- Components with React Testing Library
- API functions with mocked fetch

### Integration Tests
- Wizard flow end-to-end
- API integration with MSW

### E2E Tests
- Playwright/Cypress for critical paths
