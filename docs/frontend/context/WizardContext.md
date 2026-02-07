# WizardContext

Глобальное состояние wizard flow для адаптации резюме.

## Файл

`frontend/src/context/WizardContext.tsx`

## Назначение

WizardContext управляет состоянием 4-шагового wizard:
1. **Step 1** — загрузка и парсинг резюме
2. **Step 2** — загрузка и парсинг вакансии
3. **Step 3** — анализ соответствия
4. **Step 4** — выбор и применение улучшений

## Использование

```tsx
// Обёртка в WizardPage.tsx
import { WizardProvider } from '@/context/WizardContext'

function WizardPage() {
  return (
    <WizardProvider>
      <WizardLayout>
        {/* Step components */}
      </WizardLayout>
    </WizardProvider>
  )
}

// В компоненте шага
import { useWizard } from '@/context/WizardContext'

function Step1Resume() {
  const { state, setResumeText, setResumeData, goToNextStep } = useWizard()
  // ...
}
```

## WizardState

```typescript
interface WizardState {
  // Step 1 - Resume
  resumeText: string              // Исходный текст резюме
  resumeId: string | null         // UUID из БД
  parsedResume: ParsedResume | null  // Распознанные данные
  
  // Step 2 - Vacancy
  vacancyText: string             // Исходный текст вакансии
  vacancyId: string | null        // UUID из БД
  parsedVacancy: ParsedVacancy | null  // Распознанные данные
  
  // Step 3 - Analysis
  analysis: MatchAnalysis | null  // Результат анализа
  analysisId: string | null       // UUID анализа
  previousScore: number | null    // Балл до улучшения (для сравнения)
  
  // Step 4 - Improvement
  selectedCheckboxes: string[]    // IDs выбранных улучшений
  resultText: string              // Текст улучшенного резюме
  changeLog: ChangeLogEntry[]     // Лог изменений
  safetyNotes: string[]           // Предупреждения от AI
}
```

## Actions

### Step 1 Actions

#### `setResumeText(text: string)`
Устанавливает текст резюме (до парсинга).

```tsx
const { setResumeText } = useWizard()
setResumeText(inputValue)
```

#### `setResumeData(id: string, parsed: ParsedResume)`
Сохраняет результат парсинга резюме.

```tsx
const parseMutation = useMutation({
  mutationFn: () => parseResume({ resume_text: localText }),
  onSuccess: (data) => {
    setResumeText(localText)
    setResumeData(data.resume_id, data.parsed_resume)
  },
})
```

#### `updateParsedResume(parsed: ParsedResume)`
Обновляет распознанные данные (после редактирования в UI).

```tsx
const handleParsedChange = (parsed: ParsedResume) => {
  updateParsedResume(parsed)
  setHasUnsavedChanges(true)
}
```

### Step 2 Actions

Аналогично Step 1:
- `setVacancyText(text: string)`
- `setVacancyData(id: string, parsed: ParsedVacancy)`
- `updateParsedVacancy(parsed: ParsedVacancy)`

### Step 3 Actions

#### `setAnalysis(analysisId: string, analysis: MatchAnalysis)`
Сохраняет результат анализа.

**Важно:** При повторном вызове сохраняет предыдущий score в `previousScore` для сравнения.

```typescript
const setAnalysis = useCallback((analysisId: string, analysis: MatchAnalysis) => {
  setState((prev) => ({
    ...prev,
    analysisId,
    // Save previous score for comparison (only if we already had one)
    previousScore: prev.analysis?.score ?? prev.previousScore,
    analysis,
    // Pre-select high-priority checkboxes
    selectedCheckboxes: analysis.checkbox_options
      .filter((o) => o.enabled && o.priority >= 2)
      .map((o) => o.id),
  }))
}, [])
```

### Step 4 Actions

#### `setSelectedCheckboxes(ids: string[])`
Устанавливает выбранные улучшения.

#### `toggleCheckbox(id: string)`
Переключает выбор одного checkbox.

#### `setResult(text: string, changeLog: ChangeLogEntry[], safetyNotes: string[])`
Сохраняет результат адаптации.

```tsx
const adaptMutation = useMutation({
  mutationFn: () => adaptResume({ ... }),
  onSuccess: (data) => {
    setResult(data.updated_resume_text, data.change_log, data.safety_notes)
  },
})
```

#### `applyImprovedResume(newResumeText: string)`
**Ключевая функция для итеративного улучшения.**

Делает улучшенное резюме новым базовым:
- `resumeText` ← новый текст
- Очищает `resultText`, `changeLog`, `safetyNotes`, `selectedCheckboxes`

```typescript
const applyImprovedResume = useCallback((newResumeText: string) => {
  setState((prev) => ({
    ...prev,
    resumeText: newResumeText,  // New base resume text
    resultText: '',              // Clear result
    changeLog: [],               // Clear change log
    safetyNotes: [],             // Clear safety notes
    selectedCheckboxes: [],      // Clear selections
  }))
}, [])
```

**Использование в Step 4:**
```tsx
const saveVersionMutation = useMutation({
  mutationFn: (resumeText: string) => createVersion({ ... }),
  onSuccess: (_, resumeText) => {
    applyImprovedResume(resumeText)
    reanalyzeMutation.mutate(resumeText)  // Re-run analysis
  },
})
```

### Navigation

#### `canGoToStep(step: number): boolean`
Проверяет, можно ли перейти на шаг.

```typescript
const canGoToStep = useCallback((step: number) => {
  switch (step) {
    case 1: return true
    case 2: return !!state.parsedResume      // Need parsed resume
    case 3: return !!state.parsedResume && !!state.parsedVacancy
    case 4: return !!state.analysis           // Need analysis
    default: return false
  }
}, [state.parsedResume, state.parsedVacancy, state.analysis])
```

#### `goToNextStep()`
Переход на следующий шаг (если разрешено).

#### `goToPrevStep()`
Переход на предыдущий шаг.

#### `reset()`
Сброс всего состояния к начальному.

## Patterns

### Iterative Improvement Loop

```
                    ┌─────────────────┐
                    │   Step 4        │
                    │   checkboxes    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Adapt Resume  │
                    │   (API call)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Step 4        │
                    │   review        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Confirm &     │
                    │   Save Version  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │applyImproved-   │
                    │Resume()         │◄─── resumeText = newText
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Re-analyze    │
                    │   (API call)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Step 4        │
                    │   analysis      │◄─── previousScore vs new score
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Continue        │
                    │ improving?      │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌────────────────┐            ┌────────────────┐
     │ Yes → back to  │            │ No → done      │
     │ checkboxes     │            │                │
     └────────────────┘            └────────────────┘
```

### Score Comparison

```tsx
// In WizardContext
const setAnalysis = (analysisId, analysis) => {
  setState((prev) => ({
    ...prev,
    // Save old score before overwriting
    previousScore: prev.analysis?.score ?? prev.previousScore,
    analysis,
  }))
}

// In Step4Improvement
const scoreDiff = state.previousScore !== null && analysis 
  ? analysis.score - state.previousScore 
  : null

// Display
{scoreDiff > 0 && <TrendingUp className="text-green-600" />}
{scoreDiff < 0 && <TrendingDown className="text-red-600" />}
{scoreDiff === 0 && <Minus className="text-gray-500" />}
```

## Initial State

```typescript
const initialState: WizardState = {
  resumeText: '',
  resumeId: null,
  parsedResume: null,
  vacancyText: '',
  vacancyId: null,
  parsedVacancy: null,
  analysis: null,
  analysisId: null,
  previousScore: null,
  selectedCheckboxes: [],
  resultText: '',
  changeLog: [],
  safetyNotes: [],
}
```
