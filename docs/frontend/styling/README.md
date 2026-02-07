# Styling

Система стилей и дизайн-система приложения.

## Стек

- **CSS Framework:** Tailwind CSS v3
- **Icons:** Lucide React
- **Подход:** Utility-first CSS

## Файлы конфигурации

```
frontend/
├── tailwind.config.js     # Tailwind configuration
├── postcss.config.js      # PostCSS with Tailwind plugin
├── src/
│   └── index.css          # Global styles, Tailwind imports
```

## Tailwind Configuration

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
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
```

## Global Styles

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom base styles */
@layer base {
  body {
    @apply bg-gray-50 text-gray-900 antialiased;
  }
}

/* Custom component classes */
@layer components {
  .btn-primary {
    @apply bg-primary-600 text-white px-4 py-2 rounded-lg 
           hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 
           focus:ring-offset-2 transition-colors;
  }
  
  .btn-outline {
    @apply border border-gray-300 text-gray-700 px-4 py-2 rounded-lg
           hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 
           focus:ring-offset-2 transition-colors;
  }
}
```

## Цветовая палитра

### Primary (Blue)

| Token | Hex | Usage |
|-------|-----|-------|
| `primary-50` | `#eff6ff` | Background hover |
| `primary-100` | `#dbeafe` | Active background |
| `primary-500` | `#3b82f6` | Focus rings |
| `primary-600` | `#2563eb` | Primary buttons |
| `primary-700` | `#1d4ed8` | Button hover |

### Semantic Colors

| Color | Class | Usage |
|-------|-------|-------|
| Success | `text-green-600`, `bg-green-50` | Positive states, matched skills |
| Warning | `text-yellow-600`, `bg-yellow-50` | Warnings, medium severity |
| Error | `text-red-600`, `bg-red-50` | Errors, missing skills, high severity |
| Neutral | `text-gray-*`, `bg-gray-*` | Text, backgrounds, borders |

### Score Colors

```tsx
// Color by score value
const getScoreColor = (score: number) => {
  if (score >= 70) return 'text-green-600'
  if (score >= 50) return 'text-yellow-600'
  return 'text-red-600'
}

// Progress bar color
const getBarColor = (percentage: number) => {
  if (percentage >= 70) return 'bg-green-500'
  if (percentage >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}
```

## Компонентные паттерны

### Cards

```tsx
// White card with border
<div className="bg-white border border-gray-200 rounded-lg p-4">
  {/* content */}
</div>

// Card with shadow
<div className="bg-white rounded-lg shadow-md p-6">
  {/* content */}
</div>

// Status card (colored)
<div className={`rounded-lg p-4 border ${
  status === 'success' ? 'bg-green-50 border-green-200' :
  status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
  'bg-red-50 border-red-200'
}`}>
  {/* content */}
</div>
```

### Buttons

```tsx
// Primary button
<button className="bg-primary-600 hover:bg-primary-700 text-white 
                   px-4 py-2 rounded-lg transition-colors
                   focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                   disabled:opacity-50 disabled:cursor-not-allowed">
  Primary
</button>

// Outline button
<button className="border border-gray-300 text-gray-700 
                   px-4 py-2 rounded-lg hover:bg-gray-50
                   transition-colors">
  Outline
</button>

// Ghost button
<button className="text-gray-600 px-4 py-2 rounded-lg 
                   hover:bg-gray-100 transition-colors">
  Ghost
</button>
```

### Form Elements

```tsx
// Text input
<input 
  type="text"
  className="w-full px-3 py-2 border border-gray-300 rounded-lg
             focus:ring-2 focus:ring-primary-500 focus:border-transparent
             placeholder-gray-400"
  placeholder="Enter text..."
/>

// Textarea
<textarea
  className="w-full px-3 py-2 border border-gray-300 rounded-lg
             focus:ring-2 focus:ring-primary-500 focus:border-transparent
             resize-none"
  rows={10}
/>

// Checkbox
<label className="flex items-center gap-2 cursor-pointer">
  <input type="checkbox" className="w-4 h-4 text-primary-600 
                                     rounded border-gray-300
                                     focus:ring-primary-500" />
  <span className="text-sm text-gray-700">Label</span>
</label>
```

### Badges

```tsx
// Skill badge (matched)
<span className="inline-flex items-center gap-1 px-3 py-1.5 
                 rounded-lg text-sm bg-green-50 text-green-800">
  <CheckCircle className="w-4 h-4 text-green-500" />
  Python
</span>

// Skill badge (missing)
<span className="inline-flex items-center gap-1 px-3 py-1.5 
                 rounded-lg text-sm bg-red-50 text-red-800">
  <XCircle className="w-4 h-4 text-red-500" />
  Kubernetes
</span>

// Impact badge
<span className={`text-xs px-2 py-0.5 rounded ${
  impact === 'high' ? 'bg-red-100 text-red-700' :
  impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
  'bg-gray-100 text-gray-600'
}`}>
  {impact}
</span>
```

### Progress Bar

```tsx
<div className="w-full bg-gray-200 rounded-full h-2">
  <div 
    className={`h-2 rounded-full ${
      percentage >= 70 ? 'bg-green-500' : 
      percentage >= 50 ? 'bg-yellow-500' : 
      'bg-red-500'
    }`}
    style={{ width: `${percentage}%` }}
  />
</div>
```

## Layout Patterns

### Container

```tsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  {/* content */}
</div>
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
  FileText,      // Resume/document
  Briefcase,     // Vacancy/job
  BarChart2,     // Analysis/chart
  Sparkles,      // Improvement/AI
  ArrowRight,    // Navigation
  ArrowLeft,
  Check,         // Success/confirm
  X,             // Close/reject
  AlertTriangle, // Warning
  CheckCircle,   // Matched
  XCircle,       // Missing
  TrendingUp,    // Score improved
  TrendingDown,  // Score decreased
  Minus,         // No change
  Loader2,       // Loading spinner
  Copy,          // Copy to clipboard
  RotateCcw,     // Reset
  Edit3,         // Edit
  Save,          // Save
} from 'lucide-react'
```

### Usage

```tsx
// In button
<Button>
  <Sparkles className="w-4 h-4 mr-2" />
  Улучшить
</Button>

// Standalone
<CheckCircle className="w-5 h-5 text-green-500" />

// Loading spinner
<Loader2 className="w-4 h-4 animate-spin" />
```

### Icon Sizes

| Size | Class | Usage |
|------|-------|-------|
| Small | `w-4 h-4` | In buttons, badges |
| Medium | `w-5 h-5` | Standalone icons |
| Large | `w-6 h-6` | Headers, empty states |

## Responsive Design

### Breakpoints

| Breakpoint | Min Width | Usage |
|------------|-----------|-------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |

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
<div className="animate-pulse bg-gray-200 h-4 rounded" />

// Bounce (attention)
<div className="animate-bounce" />
```

### Transitions

```tsx
// Color transition (buttons)
<button className="transition-colors duration-200 hover:bg-gray-100">

// All transitions
<div className="transition-all duration-300">

// Transform
<div className="transition-transform hover:scale-105">
```

## Dark Mode (TODO)

Пока не реализован. Для добавления:

1. Добавить `darkMode: 'class'` в `tailwind.config.js`
2. Использовать `dark:` префиксы
3. Добавить toggle в UI

```tsx
// Example
<div className="bg-white dark:bg-gray-800 
                text-gray-900 dark:text-gray-100">
```
