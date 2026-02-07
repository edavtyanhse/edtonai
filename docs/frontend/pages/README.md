# Pages

Страницы приложения и wizard flow.

## Структура

```
frontend/src/pages/
├── HomePage.tsx           # Выбор режима работы
├── WizardPage.tsx         # Контейнер wizard
├── IdealResumePage.tsx    # Генерация идеального резюме
├── History.tsx            # История версий
├── Compare.tsx            # Сравнение версий
├── Workspace.tsx          # Рабочая область (legacy)
├── index.ts               # Re-exports
│
└── wizard/                # Компоненты шагов wizard
    ├── Step1Resume.tsx
    ├── Step2Vacancy.tsx
    ├── Step3Analysis.tsx
    ├── Step4Improvement.tsx
    └── index.ts
```

---

## HomePage

Главная страница с выбором режима работы.

### Режимы

| Режим | Путь | Описание |
|-------|------|----------|
| **Адаптация резюме** | `/wizard` | 4-шаговый wizard: загрузка резюме → вакансия → анализ → улучшение |
| **Идеальное резюме** | `/ideal-resume` | Генерация образца резюме по вакансии |

### UI

```tsx
// Две карточки выбора
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
  <ModeCard
    title="Адаптация резюме"
    description="Загрузите резюме и вакансию для анализа и улучшения"
    icon={<Sparkles />}
    to="/wizard"
  />
  <ModeCard
    title="Идеальное резюме"
    description="Сгенерируйте образец резюме под вакансию"
    icon={<FileText />}
    to="/ideal-resume"
  />
</div>
```

---

## WizardPage

Контейнер для 4-шагового wizard flow.

### Структура

```tsx
function WizardPage() {
  return (
    <WizardProvider>
      <WizardContent />
    </WizardProvider>
  )
}

function WizardContent() {
  const { currentStep, setCurrentStep, canGoToStep } = useWizard()
  
  const renderStep = () => {
    switch (currentStep) {
      case 1: return <Step1Resume />
      case 2: return <Step2Vacancy />
      case 3: return <Step3Analysis />
      case 4: return <Step4Improvement />
    }
  }
  
  return (
    <WizardLayout
      currentStep={currentStep}
      onStepClick={setCurrentStep}
      canGoToStep={canGoToStep}
    >
      {renderStep()}
    </WizardLayout>
  )
}
```

### Flow

```
Step 1 (Resume) → Step 2 (Vacancy) → Step 3 (Analysis) → Step 4 (Improvement)
                                                              ↓
                                                         [Loop back]
                                                              ↓
                                                    Continue improving?
```

---

## Wizard Steps

### Step1Resume

**Файл:** `wizard/Step1Resume.tsx`

**Назначение:** Ввод и парсинг текста резюме.

#### Режимы

| Mode | Описание |
|------|----------|
| `input` | Textarea для ввода текста |
| `parsed` | Редактор распознанных данных |

#### Flow

```
┌─────────────────────┐
│   Mode: input       │
│   TextAreaWithCounter│
│   [Распознать резюме]│
└──────────┬──────────┘
           │ API: POST /v1/resumes/parse
           ▼
┌─────────────────────┐
│   Mode: parsed      │
│   ResumeEditor      │
│   [Сохранить] [Далее]│
└─────────────────────┘
```

#### Ключевой код

```tsx
const parseMutation = useMutation({
  mutationFn: () => parseResume({ resume_text: localText }),
  onSuccess: (data) => {
    setResumeText(localText)
    setResumeData(data.resume_id, data.parsed_resume)
    setMode('parsed')
  },
})

const saveMutation = useMutation({
  mutationFn: (parsed: ParsedResume) =>
    updateResume(state.resumeId!, { parsed_data: parsed }),
  onSuccess: (data) => {
    updateParsedResume(data.parsed_data)
    setHasUnsavedChanges(false)
  },
})
```

---

### Step2Vacancy

**Файл:** `wizard/Step2Vacancy.tsx`

Аналогично Step1, но для вакансии:
- `parseVacancy()` API
- `VacancyEditor` компонент

---

### Step3Analysis

**Файл:** `wizard/Step3Analysis.tsx`

**Назначение:** Анализ соответствия резюме вакансии.

#### UI Секции

1. **Preview cards** — краткая информация о резюме и вакансии
2. **Score** — общий балл (0-100) с цветовой индикацией
3. **Score Breakdown** — 4 компонента: skill_fit, experience_fit, ats_fit, clarity
4. **Skills Match** — matched/missing навыки (required + preferred)
5. **ATS Coverage** — покрытие ключевых слов
6. **Gaps** — пробелы с severity и suggestions
7. **Checkbox Options** — предпросмотр доступных улучшений

#### Ключевой код

```tsx
const analyzeMutation = useMutation({
  mutationFn: () =>
    analyzeMatch({
      resume_text: state.resumeText,
      vacancy_text: state.vacancyText,
    }),
  onSuccess: (data) => {
    setAnalysis(data.analysis_id, data.analysis)
  },
})
```

#### Helper Components

```tsx
// ScoreCard - карточка с прогресс-баром
function ScoreCard({ label, value, maxValue, comment }) {
  const percentage = (value / maxValue) * 100
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex justify-between">
        <span>{label}</span>
        <span>{value}/{maxValue}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={percentage >= 70 ? 'bg-green-500' : ...}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500">{comment}</p>
    </div>
  )
}

// SkillBadge - бейдж навыка
function SkillBadge({ skill, matched }) {
  return (
    <div className={matched ? 'bg-green-50' : 'bg-red-50'}>
      {matched ? <CheckCircle /> : <XCircle />}
      {skill}
    </div>
  )
}
```

---

### Step4Improvement

**Файл:** `wizard/Step4Improvement.tsx`

**Назначение:** Выбор и применение улучшений к резюме.

#### Режимы

| Mode | Описание |
|------|----------|
| `checkboxes` | Выбор улучшений из списка |
| `review` | Подтверждение/отклонение каждого изменения |
| `analysis` | Результат улучшения с новым анализом |

#### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mode: checkboxes                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ☑ Добавить метрики к достижениям      [high impact]     │    │
│  │ ☑ Упомянуть Agile-практики            [medium impact]   │    │
│  │ ☐ Добавить ключевые слова ATS         [low impact]      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                        [Применить улучшения]                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ API: POST /v1/resumes/adapt
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Mode: review                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Change 1: Добавлены метрики                              │    │
│  │ Where: experience                                        │    │
│  │ Before: "Оптимизировал систему"                          │    │
│  │ After:  "Оптимизировал систему, сократив время на 40%"  │    │
│  │                                          [✓ Confirm] [✗] │    │
│  └─────────────────────────────────────────────────────────┘    │
│                        [Применить (2)]                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │ API: POST /v1/versions
                               │ API: POST /v1/match/analyze
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Mode: analysis                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Новый балл: 78/100                  Было: 65 → +13 ↑    │    │
│  └─────────────────────────────────────────────────────────┘    │
│  • Score Breakdown                                               │
│  • Skills Match                                                  │
│  • Remaining Gaps                                                │
│                [Начать заново] [Продолжить улучшение]            │
└─────────────────────────────────────────────────────────────────┘
```

#### Ключевые функции

```tsx
// Применение улучшений
const adaptMutation = useMutation({
  mutationFn: () =>
    adaptResume({
      resume_text: state.resumeText,
      vacancy_text: state.vacancyText,
      selected_checkbox_ids: state.selectedCheckboxes,
    }),
  onSuccess: (data) => {
    setResult(data.updated_resume_text, data.change_log, data.safety_notes)
    setPendingChanges(data.change_log.map(e => ({ ...e, status: 'pending' })))
    setMode('review')
  },
})

// Повторный анализ после подтверждения
const reanalyzeMutation = useMutation({
  mutationFn: (newResumeText: string) =>
    analyzeMatch({
      resume_text: newResumeText,
      vacancy_text: state.vacancyText,
    }),
  onSuccess: (data) => {
    setAnalysis(data.analysis_id, data.analysis)
    setMode('analysis')
  },
})

// Сохранение и переход к анализу
const saveVersionMutation = useMutation({
  mutationFn: (resumeText: string) =>
    createVersion({
      type: 'adapt',
      title: versionTitle || undefined,
      resume_text: state.resumeText,
      vacancy_text: state.vacancyText,
      result_text: resumeText,
      selected_checkbox_ids: state.selectedCheckboxes,
    }),
  onSuccess: (_, resumeText) => {
    applyImprovedResume(resumeText)  // Make new base
    reanalyzeMutation.mutate(resumeText)
  },
})
```

#### Score Comparison

```tsx
const scoreDiff = state.previousScore !== null && analysis 
  ? analysis.score - state.previousScore 
  : null

// Display
{scoreDiff > 0 && (
  <span className="text-green-600">
    <TrendingUp /> +{scoreDiff}
  </span>
)}
{scoreDiff < 0 && (
  <span className="text-red-600">
    <TrendingDown /> {scoreDiff}
  </span>
)}
```

#### Iterative Improvement

```tsx
const handleContinueImproving = () => {
  // Go back to checkbox selection for more improvements
  setMode('checkboxes')
}
```

---

## IdealResumePage

**Файл:** `IdealResumePage.tsx`

**Назначение:** Генерация идеального образца резюме по вакансии.

### Flow

```
1. Ввод текста вакансии
2. Выбор опций (язык, шаблон)
3. API: POST /v1/resumes/ideal
4. Отображение сгенерированного резюме
5. Копирование / сохранение
```

### UI

```tsx
<div className="grid grid-cols-2 gap-6">
  <div>
    <TextAreaWithCounter
      value={vacancyText}
      onChange={setVacancyText}
      label="Текст вакансии"
    />
    <div className="flex gap-4">
      <Select label="Язык" options={['ru', 'en', 'auto']} />
      <Select label="Шаблон" options={['default', 'harvard']} />
    </div>
    <Button onClick={generate}>Сгенерировать</Button>
  </div>
  
  <div>
    <h2>Идеальное резюме</h2>
    <pre>{idealResume}</pre>
    <Button onClick={copy}>Копировать</Button>
  </div>
</div>
```

---

## History

**Файл:** `History.tsx`

**Назначение:** Список сохранённых версий резюме.

### API

```tsx
const { data: versions } = useQuery({
  queryKey: ['versions'],
  queryFn: () => getVersions(50, 0),
})
```

### UI

```tsx
<table>
  <thead>
    <tr>
      <th>Название</th>
      <th>Тип</th>
      <th>Дата</th>
      <th>Действия</th>
    </tr>
  </thead>
  <tbody>
    {versions.items.map(v => (
      <tr key={v.id}>
        <td>{v.title || 'Без названия'}</td>
        <td>{v.type}</td>
        <td>{formatDate(v.created_at)}</td>
        <td>
          <Button onClick={() => view(v.id)}>Просмотр</Button>
          <Button onClick={() => remove(v.id)}>Удалить</Button>
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

---

## Compare

**Файл:** `Compare.tsx`

**Назначение:** Сравнение двух версий резюме.

### Flow

1. Выбрать версию A (dropdown)
2. Выбрать версию B (dropdown)
3. Отобразить diff

### UI

```tsx
<div className="grid grid-cols-2 gap-4">
  <VersionSelector value={versionA} onChange={setVersionA} />
  <VersionSelector value={versionB} onChange={setVersionB} />
</div>

<DiffViewer
  before={versionA?.result_text || ''}
  after={versionB?.result_text || ''}
  mode="split"
/>
```
