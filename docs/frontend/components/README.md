# Components

Переиспользуемые UI компоненты.

## Файлы

```
frontend/src/components/
├── Button.tsx
├── CheckboxList.tsx
├── ConfirmDialog.tsx
├── CoverLetterModal.tsx
├── DiffViewer.tsx
├── ErrorBoundary.tsx
├── Layout.tsx
├── ResumeEditor.tsx
├── TextAreaWithCounter.tsx
├── Toast.tsx
├── VacancyEditor.tsx
├── WizardLayout.tsx
└── index.ts
```

---

## Button

Универсальная кнопка с вариантами стилей.

### Props

| Prop        | Type                                                           | Default     | Description      |
| ----------- | -------------------------------------------------------------- | ----------- | ---------------- |
| `variant`   | `'primary' \| 'secondary' \| 'danger' \| 'ghost' \| 'outline'` | `'primary'` | Визуальный стиль |
| `size`      | `'sm' \| 'md' \| 'lg'`                                         | `'md'`      | Размер кнопки    |
| `disabled`  | `boolean`                                                      | `false`     | Disabled state   |
| `className` | `string`                                                       | `''`        | Доп. CSS классы  |
| `children`  | `ReactNode`                                                    | -           | Содержимое       |

### Использование

```tsx
import { Button } from '@/components'

// Primary (default)
<Button onClick={handleClick}>Сохранить</Button>

// Outline
<Button variant="outline" onClick={goBack}>
  <ArrowLeft className="w-4 h-4 mr-2" />
  Назад
</Button>

// Ghost (минимальный стиль)
<Button variant="ghost" size="sm">Отмена</Button>

// Secondary
<Button variant="secondary">Экспорт</Button>

// Danger
<Button variant="danger">Удалить</Button>

// Loading state
<Button disabled={isPending}>
  {isPending ? (
    <>
      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      Загрузка...
    </>
  ) : (
    'Отправить'
  )}
</Button>
```

### Стили

| Variant     | Background           | Border                 | Text                  |
| ----------- | -------------------- | ---------------------- | --------------------- |
| `primary`   | `bg-app-accent`      | transparent            | `text-white`          |
| `secondary` | `bg-app-surface`     | `border-app-border`    | `text-app-text`       |
| `danger`    | `bg-app-danger-soft` | `border-app-danger/30` | `text-app-danger`     |
| `outline`   | transparent          | `border-app-border`    | `text-app-text-muted` |
| `ghost`     | transparent          | none                   | `text-app-text-muted` |

Не переопределяй цветовую схему primary-кнопки raw классами вроде
`bg-slate-200`, если нужна светлая кнопка: используй `variant="secondary"` или
`variant="outline"`.

---

## TextAreaWithCounter

Textarea с счётчиком символов и лимитом.

### Props

| Prop          | Type                      | Required | Description             |
| ------------- | ------------------------- | -------- | ----------------------- |
| `value`       | `string`                  | ✅       | Текущее значение        |
| `onChange`    | `(value: string) => void` | ✅       | Callback изменения      |
| `maxLength`   | `number`                  | ✅       | Максимум символов       |
| `label`       | `string`                  | ❌       | Label над полем         |
| `placeholder` | `string`                  | ❌       | Placeholder             |
| `minHeight`   | `number`                  | ❌       | Минимальная высота (px) |
| `disabled`    | `boolean`                 | ❌       | Disabled state          |

### Использование

```tsx
import { TextAreaWithCounter } from "@/components";

<TextAreaWithCounter
  value={resumeText}
  onChange={setResumeText}
  maxLength={15000}
  label="Текст резюме"
  placeholder="Вставьте текст резюме..."
  minHeight={400}
/>;
```

### Поведение

- Показывает `{current}/{max}` символов
- При превышении лимита — красный цвет счётчика
- Автоматический resize по содержимому (опционально)

---

## CheckboxList

Список checkbox-опций для выбора улучшений.

### Props

| Prop       | Type                      | Required | Description             |
| ---------- | ------------------------- | -------- | ----------------------- |
| `options`  | `CheckboxOption[]`        | ✅       | Массив опций из анализа |
| `selected` | `string[]`                | ✅       | IDs выбранных опций     |
| `onChange` | `(ids: string[]) => void` | ✅       | Callback при изменении  |

### CheckboxOption

```typescript
interface CheckboxOption {
  id: string;
  label: string;
  description: string;
  category: string;
  impact: "low" | "medium" | "high";
  requires_user_input: boolean;
  user_input_placeholder: string | null;
  priority?: number;
  enabled?: boolean;
}
```

### Использование

```tsx
import { CheckboxList } from "@/components";

<CheckboxList
  options={analysis.checkbox_options}
  selected={selectedCheckboxes}
  onChange={setSelectedCheckboxes}
/>;
```

### Визуализация

- **impact=high** — заметная danger-карточка: фон, левая полоса, badge
- **impact=medium** — warning-карточка
- **impact=low** — нейтральная карточка
- **requires_user_input=true** — warning badge и раскрываемое поле ввода

Цвета карточек строятся на `app-*` theme tokens, поэтому light/dark темы должны
проверяться вместе.

---

## ConfirmDialog

Модальное окно подтверждения.

### Props

| Prop          | Type         | Required | Description                |
| ------------- | ------------ | -------- | -------------------------- |
| `isOpen`      | `boolean`    | ✅       | Показать/скрыть            |
| `title`       | `string`     | ✅       | Заголовок                  |
| `message`     | `ReactNode`  | ✅       | Содержимое (текст или JSX) |
| `confirmText` | `string`     | ❌       | Текст кнопки подтверждения |
| `cancelText`  | `string`     | ❌       | Текст кнопки отмены        |
| `onConfirm`   | `() => void` | ✅       | Callback подтверждения     |
| `onClose`     | `() => void` | ✅       | Callback закрытия          |

### Использование

```tsx
import { ConfirmDialog } from '@/components'

const [showDialog, setShowDialog] = useState(false)

<ConfirmDialog
  isOpen={showDialog}
  title="Применить изменения"
  message={
    <div className="space-y-3">
      <p>Применить {count} изменений?</p>
      <input
        type="text"
        className="w-full px-3 py-2 border rounded-lg"
        placeholder="Название версии"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
    </div>
  }
  confirmText="Применить"
  onConfirm={handleConfirm}
  onClose={() => setShowDialog(false)}
/>
```

---

## ResumeEditor

Форма редактирования распознанных данных резюме.

### Props

| Prop       | Type                           | Required | Description         |
| ---------- | ------------------------------ | -------- | ------------------- |
| `data`     | `ParsedResume`                 | ✅       | Распознанные данные |
| `onChange` | `(data: ParsedResume) => void` | ✅       | Callback изменения  |

### Секции

- **Personal Info** — имя, должность, локация, контакты
- **Summary** — краткое описание
- **Skills** — навыки с категориями и уровнями
- **Work Experience** — места работы с датами, обязанностями, достижениями
- **Education** — образование
- **Certifications** — сертификаты
- **Languages** — языки

### Использование

```tsx
import ResumeEditor from "@/components/ResumeEditor";

<ResumeEditor
  data={parsedResume}
  onChange={(updated) => {
    updateParsedResume(updated);
    setHasUnsavedChanges(true);
  }}
/>;
```

---

## VacancyEditor

Аналогично ResumeEditor, но для вакансии.

### Props

| Prop       | Type                            | Required | Description         |
| ---------- | ------------------------------- | -------- | ------------------- |
| `data`     | `ParsedVacancy`                 | ✅       | Распознанные данные |
| `onChange` | `(data: ParsedVacancy) => void` | ✅       | Callback изменения  |

### Секции

- **Job Info** — название, компания, тип занятости, локация
- **Required Skills** — обязательные навыки
- **Preferred Skills** — желательные навыки
- **Experience Requirements** — требования к опыту
- **Responsibilities** — обязанности
- **ATS Keywords** — ключевые слова

---

## DiffViewer

Показ различий между двумя текстами.

### Props

| Prop     | Type                  | Required | Description       |
| -------- | --------------------- | -------- | ----------------- |
| `before` | `string`              | ✅       | Исходный текст    |
| `after`  | `string`              | ✅       | Изменённый текст  |
| `mode`   | `'inline' \| 'split'` | ❌       | Режим отображения |

### Использование

```tsx
import { DiffViewer } from "@/components";

<DiffViewer before={originalResume} after={improvedResume} mode="split" />;
```

---

## Layout

Обёртка страниц с header и навигацией.

### Структура

```tsx
<div className="min-h-screen flex flex-col">
  <header>
    <Logo />
    <Navigation />
  </header>

  <main className="flex-1 p-6">
    <div className="max-w-7xl mx-auto">
      <Outlet /> {/* React Router outlet */}
    </div>
  </main>
</div>
```

### Навигация

- `/` — Workspace
- `/history` — History
- `/compare` — Compare

---

## WizardLayout

Layout для wizard flow с боковой панелью шагов.

### Props

| Prop          | Type                        | Required | Description            |
| ------------- | --------------------------- | -------- | ---------------------- |
| `currentStep` | `number`                    | ✅       | Текущий шаг (1-4)      |
| `onStepClick` | `(step: number) => void`    | ✅       | Callback клика по шагу |
| `canGoToStep` | `(step: number) => boolean` | ✅       | Можно ли перейти       |
| `children`    | `ReactNode`                 | ✅       | Контент текущего шага  |

### Шаги

1. **Резюме** — иконка FileText
2. **Вакансия** — иконка Briefcase
3. **Анализ** — иконка BarChart2
4. **Улучшение** — иконка Sparkles

### Состояния шага

- **completed** — зелёная галочка
- **current** — синяя подсветка
- **available** — кликабельный
- **disabled** — серый, некликабельный

---

## Toast / Toaster

Система уведомлений.

### Setup

```tsx
// App.tsx
import { Toaster } from "@/components/Toast";

function App() {
  return (
    <>
      <Routes>...</Routes>
      <Toaster />
    </>
  );
}
```

### Использование

```tsx
import { toast } from "@/components/Toast";

// Success
toast.success("Резюме сохранено!");

// Error
toast.error("Ошибка при парсинге");

// Info
toast.info("Обработка...");

// With duration
toast.success("Готово!", { duration: 5000 });
```

---

## ErrorBoundary

Обработка React ошибок.

### Использование

```tsx
import { ErrorBoundary } from "@/components";

<ErrorBoundary>
  <App />
</ErrorBoundary>;
```

### Fallback UI

При ошибке показывает:

- Сообщение об ошибке
- Кнопка "Попробовать снова" (reset)
- Ссылка на главную

---

## CoverLetterModal

Модальное окно отображения сгенерированного сопроводительного письма.

### Props

| Prop             | Type                   | Required | Description                       |
| ---------------- | ---------------------- | -------- | --------------------------------- |
| `isOpen`         | `boolean`              | ✅       | Показать/скрыть                   |
| `onClose`        | `() => void`           | ✅       | Callback закрытия                 |
| `coverLetter`    | `string`               | ✅       | Полный текст письма               |
| `structure`      | `CoverLetterStructure` | ❌       | Структура: opening, body, closing |
| `keyPoints`      | `string[]`             | ❌       | Использованные факты из резюме    |
| `alignmentNotes` | `string[]`             | ❌       | Соответствие вакансии             |
| `isLoading`      | `boolean`              | ❌       | Состояние загрузки                |

### Секции модала

1. **Полный текст письма** — в блоке `pre` с сохранением форматирования
2. **Структура письма** — три цветных карточки (вступление, основная часть, заключение)
3. **Использованные факты** — список навыков и фактов из резюме
4. **Соответствие вакансии** — как письмо адресует требования

### Действия

- **Копировать** — копирует текст в буфер обмена
- **Скачать** — скачивает как `.txt` файл (`cover-letter-YYYY-MM-DD.txt`)

### Использование

```tsx
import { CoverLetterModal } from "@/components";

<CoverLetterModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  coverLetter={data.cover_letter_text}
  structure={data.structure}
  keyPoints={data.key_points_used}
  alignmentNotes={data.alignment_notes}
/>;
```

---

## Index Re-exports

```typescript
// components/index.ts
export { default as Button } from "./Button";
export { default as TextAreaWithCounter } from "./TextAreaWithCounter";
export { default as CheckboxList } from "./CheckboxList";
export { default as ConfirmDialog } from "./ConfirmDialog";
export { default as DiffViewer } from "./DiffViewer";
export { default as Layout } from "./Layout";
export { default as WizardLayout } from "./WizardLayout";
export { default as ResumeEditor } from "./ResumeEditor";
export { default as VacancyEditor } from "./VacancyEditor";
export { ErrorBoundary } from "./ErrorBoundary";
export { Toaster, toast } from "./Toast";
export { CoverLetterModal } from "./CoverLetterModal";
```

### Import

```tsx
// Single import
import { Button, TextAreaWithCounter, CheckboxList } from "@/components";
```
