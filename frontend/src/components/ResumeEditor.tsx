import { useState } from 'react'
import { Plus, X, ChevronDown, ChevronUp } from 'lucide-react'
import type { ParsedResume, WorkExperience, Education, Skill } from '@/api'

interface ResumeEditorProps {
  data: ParsedResume
  onChange: (data: ParsedResume) => void
  readonly?: boolean
}

export default function ResumeEditor({ data, onChange, readonly = false }: ResumeEditorProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    personal: true,
    summary: true,
    skills: true,
    experience: true,
    education: false,
    certifications: false,
    languages: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const updatePersonalInfo = (field: string, value: string) => {
    onChange({
      ...data,
      personal_info: { ...data.personal_info, [field]: value },
    })
  }

  const updateContact = (key: string, value: string) => {
    onChange({
      ...data,
      personal_info: {
        ...data.personal_info,
        contacts: { ...data.personal_info?.contacts, [key]: value },
      },
    })
  }

  const updateSummary = (value: string) => {
    onChange({ ...data, summary: value })
  }

  const updateSkills = (skills: Skill[]) => {
    onChange({ ...data, skills })
  }

  const updateExperience = (index: number, exp: WorkExperience) => {
    const newExperience = [...(data.work_experience || [])]
    newExperience[index] = exp
    onChange({ ...data, work_experience: newExperience })
  }

  const addExperience = () => {
    onChange({
      ...data,
      work_experience: [
        ...(data.work_experience || []),
        { company: '', title: '', responsibilities: [], achievements: [], tech_stack: [] },
      ],
    })
  }

  const removeExperience = (index: number) => {
    const newExperience = [...(data.work_experience || [])]
    newExperience.splice(index, 1)
    onChange({ ...data, work_experience: newExperience })
  }

  const updateEducation = (index: number, edu: Education) => {
    const newEducation = [...(data.education || [])]
    newEducation[index] = edu
    onChange({ ...data, education: newEducation })
  }

  const addEducation = () => {
    onChange({
      ...data,
      education: [...(data.education || []), { institution: '', degree: '', field_of_study: '' }],
    })
  }

  const removeEducation = (index: number) => {
    const newEducation = [...(data.education || [])]
    newEducation.splice(index, 1)
    onChange({ ...data, education: newEducation })
  }

  return (
    <div className="space-y-4">
      {/* Personal Info */}
      <Section
        title="Личная информация"
        expanded={expandedSections.personal}
        onToggle={() => toggleSection('personal')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InputField
            label="Имя"
            value={data.personal_info?.name || ''}
            onChange={(v) => updatePersonalInfo('name', v)}
            readonly={readonly}
          />
          <InputField
            label="Должность"
            value={data.personal_info?.title || ''}
            onChange={(v) => updatePersonalInfo('title', v)}
            readonly={readonly}
          />
          <InputField
            label="Локация"
            value={data.personal_info?.location || ''}
            onChange={(v) => updatePersonalInfo('location', v)}
            readonly={readonly}
          />
          <InputField
            label="Email"
            value={data.personal_info?.contacts?.email || ''}
            onChange={(v) => updateContact('email', v)}
            readonly={readonly}
          />
          <InputField
            label="Телефон"
            value={data.personal_info?.contacts?.phone || ''}
            onChange={(v) => updateContact('phone', v)}
            readonly={readonly}
          />
          <InputField
            label="LinkedIn"
            value={data.personal_info?.contacts?.linkedin || ''}
            onChange={(v) => updateContact('linkedin', v)}
            readonly={readonly}
          />
        </div>
      </Section>

      {/* Summary */}
      <Section
        title="Саммари / О себе"
        expanded={expandedSections.summary}
        onToggle={() => toggleSection('summary')}
      >
        <textarea
          className={`w-full px-3 py-2 border rounded-lg resize-none ${readonly ? 'bg-slate-900/50 border-slate-700 cursor-not-allowed text-slate-400' : 'bg-slate-900 border-slate-700 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent'
            }`}
          rows={4}
          value={data.summary || ''}
          onChange={(e) => updateSummary(e.target.value)}
          readOnly={readonly}
          placeholder="Краткое описание профессионального опыта..."
        />
      </Section>

      {/* Skills */}
      <Section
        title={`Навыки (${data.skills?.length || 0})`}
        expanded={expandedSections.skills}
        onToggle={() => toggleSection('skills')}
      >
        <SkillTagEditor
          skills={data.skills || []}
          onChange={updateSkills}
          readonly={readonly}
          placeholder="Добавить навык..."
        />
      </Section>

      {/* Work Experience */}
      <Section
        title={`Опыт работы (${data.work_experience?.length || 0})`}
        expanded={expandedSections.experience}
        onToggle={() => toggleSection('experience')}
      >
        <div className="space-y-4">
          {data.work_experience?.map((exp, index) => (
            <ExperienceItem
              key={index}
              experience={exp}
              onChange={(e) => updateExperience(index, e)}
              onRemove={() => removeExperience(index)}
              readonly={readonly}
            />
          ))}
          {!readonly && (
            <button
              onClick={addExperience}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus className="w-4 h-4" /> Добавить место работы
            </button>
          )}
        </div>
      </Section>

      {/* Education */}
      <Section
        title={`Образование (${data.education?.length || 0})`}
        expanded={expandedSections.education}
        onToggle={() => toggleSection('education')}
      >
        <div className="space-y-4">
          {data.education?.map((edu, index) => (
            <EducationItem
              key={index}
              education={edu}
              onChange={(e) => updateEducation(index, e)}
              onRemove={() => removeEducation(index)}
              readonly={readonly}
            />
          ))}
          {!readonly && (
            <button
              onClick={addEducation}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus className="w-4 h-4" /> Добавить образование
            </button>
          )}
        </div>
      </Section>

      {/* Languages */}
      <Section
        title={`Языки (${data.languages?.length || 0})`}
        expanded={expandedSections.languages}
        onToggle={() => toggleSection('languages')}
      >
        <LanguageEditor
          languages={data.languages || []}
          onChange={(langs) => onChange({ ...data, languages: langs })}
          readonly={readonly}
        />
      </Section>
    </div>
  )
}

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
        className={`w-full px-3 py-2 border rounded-lg transition-colors ${readonly
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
}: {
  tags: string[]
  onChange: (tags: string[]) => void
  readonly?: boolean
  placeholder?: string
}) {
  const [input, setInput] = useState('')

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
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
          >
            {tag}
            {!readonly && (
              <button onClick={() => handleRemove(tag)} className="hover:text-blue-900">
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

// Skill tag editor that handles Skill objects with {name, level, category}
function SkillTagEditor({
  skills,
  onChange,
  readonly = false,
  placeholder = 'Добавить...',
}: {
  skills: Skill[]
  onChange: (skills: Skill[]) => void
  readonly?: boolean
  placeholder?: string
}) {
  const [input, setInput] = useState('')

  const handleAdd = () => {
    const trimmed = input.trim()
    if (trimmed && !skills.some(s => s.name === trimmed)) {
      onChange([...skills, { name: trimmed, level: 'unknown', category: 'other' }])
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

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'language': return 'bg-purple-100 text-purple-800'
      case 'framework': return 'bg-blue-100 text-blue-800'
      case 'database': return 'bg-green-100 text-green-800'
      case 'cloud': return 'bg-yellow-100 text-yellow-800'
      case 'devops': return 'bg-orange-100 text-orange-800'
      case 'tool': return 'bg-gray-100 text-gray-800'
      case 'soft': return 'bg-pink-100 text-pink-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {skills.map((skill) => (
          <span
            key={skill.name}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm ${getCategoryColor(skill.category)}`}
            title={skill.level ? `Level: ${skill.level}` : undefined}
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

function ExperienceItem({
  experience,
  onChange,
  onRemove,
  readonly = false,
}: {
  experience: WorkExperience
  onChange: (exp: WorkExperience) => void
  onRemove: () => void
  readonly?: boolean
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-start">
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField
            label="Компания"
            value={experience.company}
            onChange={(v) => onChange({ ...experience, company: v })}
            readonly={readonly}
          />
          <InputField
            label="Должность"
            value={experience.title}
            onChange={(v) => onChange({ ...experience, title: v })}
            readonly={readonly}
          />
          <InputField
            label="Дата начала"
            value={experience.start_date || ''}
            onChange={(v) => onChange({ ...experience, start_date: v })}
            readonly={readonly}
          />
          <InputField
            label="Дата окончания"
            value={experience.end_date || ''}
            onChange={(v) => onChange({ ...experience, end_date: v })}
            readonly={readonly}
          />
        </div>
        {!readonly && (
          <button onClick={onRemove} className="ml-2 text-red-500 hover:text-red-700">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Обязанности и достижения
        </label>
        <textarea
          className={`w-full px-3 py-2 border rounded-lg resize-none ${readonly ? 'bg-slate-900/50 border-slate-700 cursor-not-allowed text-slate-400' : 'bg-slate-900 border-slate-700 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent'
            }`}
          rows={3}
          value={[...(experience.responsibilities || []), ...(experience.achievements || [])].join('\n')}
          onChange={(e) => {
            const lines = e.target.value.split('\n').filter((l) => l.trim())
            onChange({ ...experience, responsibilities: lines, achievements: [] })
          }}
          readOnly={readonly}
          placeholder="По одному пункту на строку..."
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Технологии</label>
        <TagEditor
          tags={experience.tech_stack || []}
          onChange={(tech_stack) => onChange({ ...experience, tech_stack })}
          readonly={readonly}
          placeholder="Добавить технологию..."
        />
      </div>
    </div>
  )
}

function EducationItem({
  education,
  onChange,
  onRemove,
  readonly = false,
}: {
  education: Education
  onChange: (edu: Education) => void
  onRemove: () => void
  readonly?: boolean
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField
            label="Учебное заведение"
            value={education.institution}
            onChange={(v) => onChange({ ...education, institution: v })}
            readonly={readonly}
          />
          <InputField
            label="Степень"
            value={education.degree || ''}
            onChange={(v) => onChange({ ...education, degree: v })}
            readonly={readonly}
          />
          <InputField
            label="Специальность"
            value={education.field_of_study || ''}
            onChange={(v) => onChange({ ...education, field_of_study: v })}
            readonly={readonly}
          />
          <InputField
            label="Годы обучения"
            value={`${education.start_date || ''} - ${education.end_date || ''}`}
            onChange={(v) => {
              const [start, end] = v.split(' - ')
              onChange({ ...education, start_date: start?.trim(), end_date: end?.trim() })
            }}
            readonly={readonly}
          />
        </div>
        {!readonly && (
          <button onClick={onRemove} className="ml-2 text-red-500 hover:text-red-700">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  )
}

function LanguageEditor({
  languages,
  onChange,
  readonly = false,
}: {
  languages: any[] // Accept string or object for compatibility
  onChange: (languages: any[]) => void
  readonly?: boolean
}) {
  const [input, setInput] = useState('')
  const [proficiency, setProficiency] = useState('')

  const handleAdd = () => {
    if (input.trim()) {
      // Always add as object now
      const newLang = { language: input.trim(), proficiency: proficiency.trim() || undefined }
      onChange([...languages, newLang])
      setInput('')
      setProficiency('')
    }
  }

  const handleRemove = (index: number) => {
    const newLangs = [...languages]
    newLangs.splice(index, 1)
    onChange(newLangs)
  }

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {languages.map((l, index) => {
          const displayText = typeof l === 'string'
            ? l
            : `${l.language}${l.proficiency ? ` (${l.proficiency})` : ''}`

          return (
            <div key={index} className="flex items-center justify-between bg-slate-800 p-2 rounded border border-slate-700">
              <span className="text-white">{displayText}</span>
              {!readonly && (
                <button onClick={() => handleRemove(index)} className="text-red-400 hover:text-red-300">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          )
        })}
      </div>

      {!readonly && (
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-3 py-2 border border-slate-700 bg-slate-900 text-white rounded-lg"
            placeholder="Язык (English)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <input
            type="text"
            className="w-1/3 px-3 py-2 border border-slate-700 bg-slate-900 text-white rounded-lg"
            placeholder="Уровень (B2)"
            value={proficiency}
            onChange={(e) => setProficiency(e.target.value)}
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
