# Styling

Система стилей и дизайн-система приложения.

## Стек

- **CSS Framework:** Tailwind CSS v3
- **Icons:** Lucide React
- **Подход:** Utility-first CSS + semantic theme tokens
- **Темы:** light/dark через `next-themes`, класс `html.dark` и CSS variables

## Файлы конфигурации

```
frontend/
├── tailwind.config.js     # Tailwind configuration
├── postcss.config.js      # PostCSS with Tailwind plugin
├── src/
│   └── index.css          # Global styles, Tailwind imports
```

## Theme Tokens

Цвета интерфейса задаются не прямыми `slate/blue/green` классами, а semantic
tokens. Значения токенов объявлены в `frontend/src/index.css` для `:root`
(light theme) и `html.dark` (dark theme), а Tailwind подключает их через
`frontend/tailwind.config.js`.

### Основные токены

| Token class                               | Назначение                                      |
| ----------------------------------------- | ----------------------------------------------- |
| `bg-app-bg`                               | Фон страницы                                    |
| `bg-app-surface`                          | Основная поверхность: карточки, модалки, header |
| `bg-app-surface-muted`                    | Вторичная поверхность, hover, readonly поля     |
| `border-app-border`                       | Обычная рамка                                   |
| `border-app-border-strong`                | Более заметная рамка/hover                      |
| `text-app-text`                           | Основной текст                                  |
| `text-app-text-muted`                     | Вторичный текст                                 |
| `text-app-text-subtle`                    | Подписи, счетчики, muted text                   |
| `bg-app-accent`, `text-app-accent`        | Основной brand/accent                           |
| `bg-app-accent-soft`                      | Мягкий accent-фон                               |
| `bg-app-icon-tile`, `text-app-accent`     | Плашки с иконками                               |
| `text-app-success`, `bg-app-success-soft` | Успех/добавления/matched                        |
| `text-app-warning`, `bg-app-warning-soft` | Предупреждения/medium severity                  |
| `text-app-danger`, `bg-app-danger-soft`   | Ошибки/удаления/high severity                   |

Правило: новые UI-компоненты должны использовать `app-*` tokens или существующие
shared-компоненты (`Button`, `TextAreaWithCounter`, `ConfirmDialog`, `Toast`).
Прямые цвета Tailwind (`text-blue-400`, `bg-slate-800`, `dark:*`) допустимы
только для редких декоративных деталей, где обе темы проверены вручную.

## Tailwind Configuration

```js
// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "rgb(var(--color-app-bg) / <alpha-value>)",
          surface: "rgb(var(--color-app-surface) / <alpha-value>)",
          "surface-muted":
            "rgb(var(--color-app-surface-muted) / <alpha-value>)",
          border: "rgb(var(--color-app-border) / <alpha-value>)",
          text: "rgb(var(--color-app-text) / <alpha-value>)",
          accent: "rgb(var(--color-app-accent) / <alpha-value>)",
          success: "rgb(var(--color-app-success) / <alpha-value>)",
          warning: "rgb(var(--color-app-warning) / <alpha-value>)",
          danger: "rgb(var(--color-app-danger) / <alpha-value>)",
        },
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
      },
    },
  },
  plugins: [],
};
```

## Global Styles

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-app-bg: 246 248 251;
  --color-app-surface: 255 255 255;
  --color-app-text: 15 23 42;
  --color-app-accent: 29 78 216;
  color-scheme: light;
}

html.dark {
  --color-app-bg: 15 23 42;
  --color-app-surface: 30 41 59;
  --color-app-text: 248 250 252;
  --color-app-accent: 96 165 250;
  color-scheme: dark;
}
```

## Цветовая палитра

### Brand / Primary

`primary-*` и `brand-*` остаются в Tailwind для совместимости и декоративных
деталей. Для новой UI-разметки предпочитай `app-accent`, потому что он
автоматически меняет значение между light/dark темой.

### Semantic Colors

| State   | Text                  | Soft Background        | Usage                                      |
| ------- | --------------------- | ---------------------- | ------------------------------------------ |
| Success | `text-app-success`    | `bg-app-success-soft`  | Positive states, matched skills, additions |
| Warning | `text-app-warning`    | `bg-app-warning-soft`  | Warnings, medium severity                  |
| Danger  | `text-app-danger`     | `bg-app-danger-soft`   | Errors, missing skills, removals           |
| Accent  | `text-app-accent`     | `bg-app-accent-soft`   | Brand, active states, info                 |
| Neutral | `text-app-text-muted` | `bg-app-surface-muted` | Secondary content                          |

### Score Colors

```tsx
// Color by score value
const getScoreColor = (score: number) => {
  if (score >= 70) return "text-app-success";
  if (score >= 50) return "text-app-warning";
  return "text-app-danger";
};

// Progress bar color
const getBarColor = (percentage: number) => {
  if (percentage >= 70) return "bg-app-success";
  if (percentage >= 50) return "bg-app-warning";
  return "bg-app-danger";
};
```

## Компонентные паттерны

### Cards

```tsx
// Surface card with border
<div className="bg-app-surface border border-app-border rounded-lg p-4">
  {/* content */}
</div>

// Card with shadow
<div className="bg-app-surface rounded-lg shadow-md p-6">
  {/* content */}
</div>

// Status card (colored)
<div className={`rounded-lg p-4 border ${
  status === 'success' ? 'bg-app-success-soft border-app-success/30' :
  status === 'warning' ? 'bg-app-warning-soft border-app-warning/30' :
  'bg-app-danger-soft border-app-danger/30'
}`}>
  {/* content */}
</div>
```

### Buttons

```tsx
// Primary button
<button className="bg-app-accent hover:bg-app-accent-hover text-white
                   px-4 py-2 rounded-lg transition-colors
                   focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                   disabled:opacity-50 disabled:cursor-not-allowed">
  Primary
</button>

// Outline button
<button className="border border-app-border text-app-text-muted
                   px-4 py-2 rounded-lg hover:bg-app-surface-muted
                   transition-colors">
  Outline
</button>

// Ghost button
<button className="text-app-text-muted px-4 py-2 rounded-lg
                   hover:bg-app-surface-muted hover:text-app-text transition-colors">
  Ghost
</button>
```

### Form Elements

```tsx
// Text input
<input
  type="text"
  className="w-full px-3 py-2 border border-app-border rounded-lg
             focus:ring-2 focus:ring-app-accent focus:border-transparent
             bg-app-surface text-app-text placeholder:text-app-text-subtle"
  placeholder="Enter text..."
/>

// Textarea
<textarea
  className="w-full px-3 py-2 border border-app-border rounded-lg
             focus:ring-2 focus:ring-app-accent focus:border-transparent
             bg-app-surface text-app-text
             resize-none"
  rows={10}
/>

// Checkbox
<label className="flex items-center gap-2 cursor-pointer">
  <input type="checkbox" className="w-4 h-4 text-app-accent
                                     rounded border-app-border
                                     focus:ring-app-accent" />
  <span className="text-sm text-app-text-muted">Label</span>
</label>
```

### Badges

```tsx
// Skill badge (matched)
<span className="inline-flex items-center gap-1 px-3 py-1.5
                 rounded-lg text-sm bg-app-success-soft text-app-success">
  <CheckCircle className="w-4 h-4 text-app-success" />
  Python
</span>

// Skill badge (missing)
<span className="inline-flex items-center gap-1 px-3 py-1.5
                 rounded-lg text-sm bg-app-danger-soft text-app-danger">
  <XCircle className="w-4 h-4 text-app-danger" />
  Kubernetes
</span>

// Impact badge
<span className={`text-xs px-2 py-0.5 rounded ${
  impact === 'high' ? 'bg-app-danger-soft text-app-danger' :
  impact === 'medium' ? 'bg-app-warning-soft text-app-warning' :
  'bg-app-surface-muted text-app-text-muted'
}`}>
  {impact}
</span>
```

### Progress Bar

```tsx
<div className="w-full bg-app-border rounded-full h-2">
  <div
    className={`h-2 rounded-full ${
      percentage >= 70
        ? "bg-app-success"
        : percentage >= 50
          ? "bg-app-warning"
          : "bg-app-danger"
    }`}
    style={{ width: `${percentage}%` }}
  />
</div>
```

## Layout Patterns

### Container

```tsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">{/* content */}</div>
```

### Grid

```tsx
// 2-column grid
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

// 4-column grid (score breakdown)
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  <ScoreCard />
  <ScoreCard />
  <ScoreCard />
  <ScoreCard />
</div>
```

### Flex

```tsx
// Space between
<div className="flex items-center justify-between">
  <h1>Title</h1>
  <Button>Action</Button>
</div>

// Center
<div className="flex items-center justify-center min-h-[400px]">
  <Loader />
</div>

// Gap
<div className="flex gap-2">
  <Button>One</Button>
  <Button>Two</Button>
</div>
```

### Spacing

```tsx
// Vertical stack with gap
<div className="space-y-4">
  <Card />
  <Card />
  <Card />
</div>

// Section spacing
<div className="space-y-6">
  <section>...</section>
  <section>...</section>
</div>
```

## Icons (Lucide)

### Import

```tsx
import {
  FileText, // Resume/document
  Briefcase, // Vacancy/job
  BarChart2, // Analysis/chart
  Sparkles, // Improvement/AI
  ArrowRight, // Navigation
  ArrowLeft,
  Check, // Success/confirm
  X, // Close/reject
  AlertTriangle, // Warning
  CheckCircle, // Matched
  XCircle, // Missing
  TrendingUp, // Score improved
  TrendingDown, // Score decreased
  Minus, // No change
  Loader2, // Loading spinner
  Copy, // Copy to clipboard
  RotateCcw, // Reset
  Edit3, // Edit
  Save, // Save
} from "lucide-react";
```

### Usage

```tsx
// In button
<Button>
  <Sparkles className="w-4 h-4 mr-2" />
  Улучшить
</Button>

// Standalone semantic icon
<CheckCircle className="w-5 h-5 text-app-success" />

// Loading spinner
<Loader2 className="w-4 h-4 animate-spin" />
```

### Icon Sizes

| Size   | Class     | Usage                 |
| ------ | --------- | --------------------- |
| Small  | `w-4 h-4` | In buttons, badges    |
| Medium | `w-5 h-5` | Standalone icons      |
| Large  | `w-6 h-6` | Headers, empty states |

## Responsive Design

### Breakpoints

| Breakpoint | Min Width | Usage            |
| ---------- | --------- | ---------------- |
| `sm`       | 640px     | Mobile landscape |
| `md`       | 768px     | Tablet           |
| `lg`       | 1024px    | Desktop          |
| `xl`       | 1280px    | Large desktop    |

### Patterns

```tsx
// Hide on mobile
<div className="hidden md:block">Desktop only</div>

// Show on mobile
<div className="md:hidden">Mobile only</div>

// Responsive columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Responsive padding
<div className="px-4 md:px-6 lg:px-8">

// Responsive text
<h1 className="text-xl md:text-2xl lg:text-3xl">
```

## Animation

### Tailwind Animations

```tsx
// Spin (loading)
<Loader2 className="animate-spin" />

// Pulse (skeleton)
<div className="animate-pulse bg-app-surface-muted h-4 rounded" />

// Bounce (attention)
<div className="animate-bounce" />
```

### Transitions

```tsx
// Color transition (buttons)
<button className="transition-colors duration-200 hover:bg-app-surface-muted">

// All transitions
<div className="transition-all duration-300">

// Transform
<div className="transition-transform hover:scale-105">
```

## Theme Review Checklist

Перед merge UI-изменений:

1. Используй semantic tokens (`app-*`) для текста, поверхности, рамок и состояний.
2. Не переопределяй `Button` raw фоном без смены `variant`; иначе легко получить
   белый текст на светлом фоне.
3. Проверяй light и dark тему для новых карточек, иконок, badge, diff/highlight.
4. Для priority/severity UI цвет должен быть виден не только в тексте: добавляй
   фон, рамку, левую полосу или icon state.
5. Для long-form текста не используй `text-app-text-subtle`; это только для
   вторичных подписей.
