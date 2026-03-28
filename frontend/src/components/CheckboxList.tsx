import { useState } from 'react'
import { Check, Sparkles, ChevronDown, ChevronUp } from 'lucide-react'
import type { CheckboxOption } from '@/api/types'

interface CheckboxListProps {
  options: CheckboxOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  userInputs?: Record<string, string>
  onUserInputChange?: (checkboxId: string, value: string) => void
  aiGenerateFlags?: Record<string, boolean>
  onAiGenerateChange?: (checkboxId: string, value: boolean) => void
}

export default function CheckboxList({
  options,
  selected,
  onChange,
  userInputs = {},
  onUserInputChange,
  aiGenerateFlags = {},
  onAiGenerateChange,
}: CheckboxListProps) {
  const [expandedInputs, setExpandedInputs] = useState<Record<string, boolean>>({})

  const handleToggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id))
    } else {
      onChange([...selected, id])
      // Auto-expand input if requires user input
      const option = options.find((o) => o.id === id)
      if (option?.requires_user_input) {
        setExpandedInputs((prev) => ({ ...prev, [id]: true }))
      }
    }
  }

  const handleInputChange = (id: string, value: string) => {
    onUserInputChange?.(id, value)
    // If user types something, disable AI generate
    if (value && onAiGenerateChange) {
      onAiGenerateChange(id, false)
    }
  }

  const handleAiGenerate = (id: string) => {
    onAiGenerateChange?.(id, true)
    // Clear user input when AI generate is selected
    onUserInputChange?.(id, '')
  }

  const toggleInputExpanded = (id: string) => {
    setExpandedInputs((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  // Group by category
  const grouped = options.reduce(
    (acc, option) => {
      const category = option.category || 'other'
      if (!acc[category]) acc[category] = []
      acc[category].push(option)
      return acc
    },
    {} as Record<string, CheckboxOption[]>
  )

  const categoryLabels: Record<string, string> = {
    skills: 'Навыки',
    experience: 'Опыт',
    ats: 'ATS оптимизация',
    format: 'Форматирование',
    content: 'Контент',
    education: 'Образование',
    other: 'Другое',
  }

  // Category order for display
  const categoryOrder = ['skills', 'experience', 'ats', 'education', 'format', 'content', 'other']

  if (options.length === 0) {
    return <div className="p-8 text-center text-slate-400">Нет доступных улучшений</div>
  }

  return (
    <div className="divide-y divide-slate-700/50">
      {categoryOrder
        .filter((cat) => grouped[cat]?.length > 0)
        .map((category) => (
          <div key={category} className="p-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
              {categoryLabels[category] || category}
            </h4>
            <div className="space-y-2">
              {grouped[category].map((option) => {
                const isSelected = selected.includes(option.id)
                const isExpanded = expandedInputs[option.id]
                const hasUserInput = !!userInputs[option.id]
                const willUseAi = aiGenerateFlags[option.id] && !hasUserInput

                return (
                  <div
                    key={option.id}
                    className={`rounded-lg border transition-all ${
                      isSelected
                        ? option.requires_user_input
                          ? 'border-amber-500/50 bg-amber-900/10'
                          : 'border-blue-500/50 bg-blue-900/10'
                        : 'border-slate-700 hover:border-slate-600 bg-slate-800 hover:bg-slate-700'
                    }`}
                  >
                    {/* Main checkbox row */}
                    <label className="flex items-start gap-3 p-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggle(option.id)}
                        className="sr-only"
                      />
                      <div
                        className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 transition-colors ${
                          isSelected
                            ? option.requires_user_input
                              ? 'bg-amber-600 border-amber-600'
                              : 'bg-blue-600 border-blue-600'
                            : 'border-slate-500 bg-slate-800'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-white">{option.label}</span>
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded ${
                              option.impact === 'high'
                                ? 'bg-red-900/30 text-red-300'
                                : option.impact === 'medium'
                                  ? 'bg-yellow-900/30 text-yellow-300'
                                  : 'bg-slate-700 text-slate-300'
                            }`}
                          >
                            {option.impact === 'high'
                              ? 'важно'
                              : option.impact === 'medium'
                                ? 'средне'
                                : 'низкий'}
                          </span>
                          {option.requires_user_input && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-900/30 text-amber-300">
                              нужен ваш ввод
                            </span>
                          )}
                          {isSelected && willUseAi && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-300 flex items-center gap-1">
                              <Sparkles className="w-3 h-3" />
                              ИИ сгенерирует
                            </span>
                          )}
                        </div>
                        {option.description && (
                          <p className="text-xs text-slate-400 mt-1">{option.description}</p>
                        )}
                      </div>

                      {/* Expand button for user input options */}
                      {isSelected && option.requires_user_input && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            toggleInputExpanded(option.id)
                          }}
                          className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </label>

                    {/* User input section */}
                    {isSelected && option.requires_user_input && isExpanded && (
                      <div className="px-3 pb-3 pt-0 ml-8 space-y-2">
                        <textarea
                          value={userInputs[option.id] || ''}
                          onChange={(e) => handleInputChange(option.id, e.target.value)}
                          placeholder={option.user_input_placeholder || 'Опишите ваш опыт...'}
                          className="w-full px-3 py-2 text-sm bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 resize-none placeholder-slate-500"
                          rows={3}
                        />
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400">
                            {hasUserInput
                              ? 'Используем ваш текст'
                              : willUseAi
                                ? 'ИИ сгенерирует общий текст'
                                : 'Введите текст или нажмите кнопку'}
                          </span>
                          {!hasUserInput && (
                            <button
                              type="button"
                              onClick={() => handleAiGenerate(option.id)}
                              className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors ${
                                willUseAi
                                  ? 'bg-purple-900/30 text-purple-300 border border-purple-500/50'
                                  : 'bg-slate-700 text-slate-300 hover:bg-purple-900/20 hover:text-purple-300 border border-slate-600'
                              }`}
                            >
                              <Sparkles className="w-3 h-3" />
                              Исправить с помощью ИИ
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
    </div>
  )
}
