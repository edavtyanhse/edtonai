import { useState } from 'react'
import { Plus, X, ChevronDown, ChevronUp } from 'lucide-react'
import type { ParsedVacancy, ExperienceRequirements, VacancySkill } from '@/api'

interface VacancyEditorProps {
  data: ParsedVacancy
  onChange: (data: ParsedVacancy) => void
  readonly?: boolean
}

export default function VacancyEditor({ data, onChange, readonly = false }: VacancyEditorProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    general: true,
    requirements: true,
    responsibilities: true,
    ats: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const updateField = (field: keyof ParsedVacancy, value: string | number | boolean | object) => {
    onChange({ ...data, [field]: value })
  }

  const updateExperienceRequirements = (
    field: keyof ExperienceRequirements,
    value: string | number
  ) => {
    onChange({
      ...data,
      experience_requirements: {
        ...data.experience_requirements,
        [field]: value,
      },
    })
  }

  return (
    <div className="space-y-4">
      {/* General Info */}
      <Section
        title="Общая информация"
        expanded={expandedSections.general}
        onToggle={() => toggleSection('general')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InputField
            label="Название вакансии"
            value={data.job_title || ''}
            onChange={(v) => updateField('job_title', v)}
            readonly={readonly}
          />
          <InputField
            label="Компания"
            value={data.company || ''}
            onChange={(v) => updateField('company', v)}
            readonly={readonly}
          />
          <InputField
            label="Тип занятости"
            value={data.employment_type || ''}
            onChange={(v) => updateField('employment_type', v)}
            readonly={readonly}
          />
          <InputField
            label="Локация"
            value={data.location || ''}
            onChange={(v) => updateField('location', v)}
            readonly={readonly}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <InputField
            label="Мин. лет опыта"
            value={data.experience_requirements?.min_years?.toString() || ''}
            onChange={(v) => updateExperienceRequirements('min_years', parseInt(v) || 0)}
            readonly={readonly}
          />
          <InputField
            label="Макс. лет опыта"
            value={data.experience_requirements?.max_years?.toString() || ''}
            onChange={(v) => updateExperienceRequirements('max_years', parseInt(v) || 0)}
            readonly={readonly}
          />
          <InputField
            label="Уровень"
            value={data.experience_requirements?.level || ''}
            onChange={(v) => updateExperienceRequirements('level', v)}
            readonly={readonly}
          />
        </div>
      </Section>

      {/* Required Skills */}
      <Section
        title={`Обязательные навыки (${data.required_skills?.length || 0})`}
        expanded={expandedSections.requirements}
        onToggle={() => toggleSection('requirements')}
      >
        <div className="space-y-4">
          <VacancySkillTagEditor
            skills={data.required_skills || []}
            onChange={(skills) => updateField('required_skills', skills)}
            readonly={readonly}
            placeholder="Добавить обязательный навык..."
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Желательные навыки ({data.preferred_skills?.length || 0})
            </label>
            <VacancySkillTagEditor
              skills={data.preferred_skills || []}
              onChange={(skills) => updateField('preferred_skills', skills)}
              readonly={readonly}
              placeholder="Добавить желательный навык..."
              variant="secondary"
            />
          </div>
        </div>
      </Section>

      {/* Responsibilities */}
      <Section
        title={`Обязанности (${data.responsibilities?.length || 0})`}
        expanded={expandedSections.responsibilities}
        onToggle={() => toggleSection('responsibilities')}
      >
        <ListEditor
          items={data.responsibilities || []}
          onChange={(items) => updateField('responsibilities', items)}
          readonly={readonly}
          placeholder="Добавить обязанность..."
        />
      </Section>

      {/* ATS Keywords */}
      <Section
        title={`ATS ключевые слова (${data.ats_keywords?.length || 0})`}
        expanded={expandedSections.ats}
        onToggle={() => toggleSection('ats')}
      >
        <TagEditor
          tags={data.ats_keywords || []}
          onChange={(keywords) => updateField('ats_keywords', keywords)}
          readonly={readonly}
          placeholder="Добавить ATS ключевое слово..."
          variant="ats"
        />
      </Section>
    </div>
  )
}

// ========================================
// Helper Components
// ========================================

// ========================================
// Helper Components
// ========================================

function Section({
  title,
  expanded,
  onToggle,
  children,
}: {
  title: string
  expanded: boolean
  onToggle: () => void
  children: React.ReactNode
}) {
  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between bg-slate-800/50 hover:bg-slate-700/50 transition-colors border-b border-slate-700/50"
      >
        <span className="font-medium text-white">{title}</span>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>
      {expanded && <div className="p-4">{children}</div>}
    </div>
  )
}

function InputField({
  label,
  value,
  onChange,
  readonly = false,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  readonly?: boolean
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-1">{label}</label>
      <input
        type="text"
        className={`w-full px-3 py-2 border rounded-lg transition-colors ${
          readonly
            ? 'bg-slate-900/50 border-slate-700 cursor-not-allowed text-slate-400'
            : 'bg-slate-900 border-slate-700 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent placeholder:text-slate-500'
        }`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readonly}
      />
    </div>
  )
}

function TagEditor({
  tags,
  onChange,
  readonly = false,
  placeholder = 'Добавить...',
  variant = 'primary',
}: {
  tags: string[]
  onChange: (tags: string[]) => void
  readonly?: boolean
  placeholder?: string
  variant?: 'primary' | 'secondary' | 'ats'
}) {
  const [input, setInput] = useState('')

  const variantStyles = {
    primary: 'bg-blue-100 text-blue-800',
    secondary: 'bg-green-100 text-green-800',
    ats: 'bg-purple-100 text-purple-800',
  }

  const handleAdd = () => {
    const trimmed = input.trim()
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed])
      setInput('')
    }
  }

  const handleRemove = (tag: string) => {
    onChange(tags.filter((t) => t !== tag))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm ${variantStyles[variant]}`}
          >
            {tag}
            {!readonly && (
              <button onClick={() => handleRemove(tag)} className="hover:opacity-70">
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}
      </div>
      {!readonly && (
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-3 py-2 border border-slate-700 bg-slate-900 text-white rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent placeholder:text-slate-500"
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleAdd}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

// VacancySkill tag editor that handles VacancySkill objects with {name, type, evidence}
function VacancySkillTagEditor({
  skills,
  onChange,
  readonly = false,
  placeholder = 'Добавить...',
  variant = 'primary',
}: {
  skills: VacancySkill[]
  onChange: (skills: VacancySkill[]) => void
  readonly?: boolean
  placeholder?: string
  variant?: 'primary' | 'secondary'
}) {
  const [input, setInput] = useState('')

  const variantStyles = {
    primary: 'bg-blue-100 text-blue-800',
    secondary: 'bg-green-100 text-green-800',
  }

  const getTypeColor = (type?: string) => {
    switch (type) {
      case 'hard':
        return 'bg-blue-100 text-blue-800'
      case 'soft':
        return 'bg-pink-100 text-pink-800'
      case 'domain':
        return 'bg-purple-100 text-purple-800'
      case 'tool':
        return 'bg-orange-100 text-orange-800'
      default:
        return variantStyles[variant]
    }
  }

  const handleAdd = () => {
    const trimmed = input.trim()
    if (trimmed && !skills.some((s) => s.name === trimmed)) {
      onChange([...skills, { name: trimmed, type: 'hard' }])
      setInput('')
    }
  }

  const handleRemove = (skillName: string) => {
    onChange(skills.filter((s) => s.name !== skillName))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {skills.map((skill) => (
          <span
            key={skill.name}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm ${getTypeColor(skill.type)}`}
            title={skill.evidence ? `Evidence: ${skill.evidence}` : undefined}
          >
            {skill.name}
            {!readonly && (
              <button onClick={() => handleRemove(skill.name)} className="hover:opacity-70">
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}
      </div>
      {!readonly && (
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-3 py-2 border border-slate-700 bg-slate-900 text-white rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent placeholder:text-slate-500"
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleAdd}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

function ListEditor({
  items,
  onChange,
  readonly = false,
  placeholder = 'Добавить...',
}: {
  items: string[]
  onChange: (items: string[]) => void
  readonly?: boolean
  placeholder?: string
}) {
  const [input, setInput] = useState('')

  const handleAdd = () => {
    const trimmed = input.trim()
    if (trimmed) {
      onChange([...items, trimmed])
      setInput('')
    }
  }

  const handleRemove = (index: number) => {
    const newItems = [...items]
    newItems.splice(index, 1)
    onChange(newItems)
  }

  const handleUpdate = (index: number, value: string) => {
    const newItems = [...items]
    newItems[index] = value
    onChange(newItems)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-2">
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            <span className="text-slate-500">•</span>
            {readonly ? (
              <span className="flex-1 text-slate-300">{item}</span>
            ) : (
              <input
                type="text"
                className="flex-1 px-2 py-1 border border-transparent hover:border-slate-600 rounded bg-transparent text-white focus:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-colors"
                value={item}
                onChange={(e) => handleUpdate(index, e.target.value)}
              />
            )}
            {!readonly && (
              <button
                onClick={() => handleRemove(index)}
                className="text-red-400 hover:text-red-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </li>
        ))}
      </ul>
      {!readonly && (
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-3 py-2 border border-slate-700 bg-slate-900 text-white rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent placeholder:text-slate-500"
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleAdd}
            className="px-3 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-500"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
