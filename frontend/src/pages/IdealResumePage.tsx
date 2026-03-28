import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  ArrowLeft, Sparkles, Loader2, Copy, Save, FileText, Settings,
  Eye, ChevronDown, Download, Check, Link as LinkIcon
} from 'lucide-react'
import { generateIdeal, createVersion, parseResume } from '@/api'
import type { ParsedResume } from '@/api'
import { Button, TextAreaWithCounter, ConfirmDialog, HeadHunterPreview } from '@/components'
import PdfPreview from '@/components/pdf/PdfPreview'

const MAX_CHARS = 10000

type Mode = 'input' | 'result'

interface Options {
  language: 'ru' | 'en' | null
  template: 'default' | 'harvard' | null
  seniority: 'junior' | 'middle' | 'senior' | null
}

// Section heading detection for formatting
const SECTION_PATTERN = /^(EDUCATION|EXPERIENCE|WORK EXPERIENCE|SKILLS|SKILLS & LANGUAGES|SUMMARY:?|ABOUT|PROJECTS|CERTIFICATIONS|LANGUAGES|ПРОФИЛЬ|ОПЫТ|ОПЫТ РАБОТЫ|ОБРАЗОВАНИЕ|НАВЫКИ|ПРОЕКТЫ|СЕРТИФИКАТЫ|ЯЗЫКИ|О СЕБЕ|КОНТАКТЫ|ДОСТИЖЕНИЯ)\s*$/i

function formatResumeText(text: string): string {
  if (!text) return ''
  const sections = [
    'EDUCATION', 'EXPERIENCE', 'WORK EXPERIENCE', 'SKILLS', 'SKILLS & LANGUAGES',
    'SUMMARY', 'SUMMARY:', 'ABOUT', 'PROJECTS', 'CERTIFICATIONS', 'LANGUAGES',
    'ПРОФИЛЬ', 'ОПЫТ', 'ОПЫТ РАБОТЫ', 'ОБРАЗОВАНИЕ', 'НАВЫКИ',
    'ПРОЕКТЫ', 'СЕРТИФИКАТЫ', 'ЯЗЫКИ', 'О СЕБЕ', 'КОНТАКТЫ', 'ДОСТИЖЕНИЯ'
  ]
  let formatted = text
  for (const section of sections) {
    const regex = new RegExp(`(\\s*\\|?\\s*)(${section.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?=\\s)`, 'gi')
    formatted = formatted.replace(regex, '\n\n$2')
  }
  formatted = formatted.replace(/\s*•\s*/g, '\n• ')
  formatted = formatted.replace(/\s+(Languages:|Technical Skills:)/g, '\n$1')
  formatted = formatted.replace(/\n{3,}/g, '\n\n').trim()
  return formatted
}

export default function IdealResumePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('input')
  const [vacancyText, setVacancyText] = useState('')
  const [vacancyUrl, setVacancyUrl] = useState('')
  const [resultText, setResultText] = useState('')
  const [metadata, setMetadata] = useState<{
    keywords_used: string[]
    structure: string[]
    assumptions: string[]
    language?: string
    template?: string
  } | null>(null)
  const [copied, setCopied] = useState(false)
  const [showOptions, setShowOptions] = useState(false)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [versionTitle, setVersionTitle] = useState('')
  const [showExportDropdown, setShowExportDropdown] = useState(false)
  const [showPdfPreview, setShowPdfPreview] = useState(false)
  const [showHhPreview, setShowHhPreview] = useState(false)
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)
  const [options, setOptions] = useState<Options>({
    language: null,
    template: null,
    seniority: null,
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      generateIdeal({
        vacancy_text: vacancyText || undefined,
        options: {
          language: options.language || undefined,
          template: options.template || undefined,
          seniority: options.seniority || undefined,
        },
      }),
    onSuccess: (data) => {
      setResultText(data.ideal_resume_text)
      setMetadata(data.metadata)
      setMode('result')
    },
  })

  const saveVersionMutation = useMutation({
    mutationFn: () =>
      createVersion({
        type: 'ideal',
        title: versionTitle || undefined,
        resume_text: '',
        vacancy_text: vacancyText,
        result_text: resultText,
        selected_checkbox_ids: [],
      }),
    onSuccess: () => {
      setShowSaveDialog(false)
      setVersionTitle('')
    },
  })

  const handleGenerate = () => {
    generateMutation.mutate()
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(resultText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExport = async (type: 'pdf' | 'hh') => {
    setShowExportDropdown(false)
    if (!parsedResume && resultText) {
      try {
        const resp = await parseResume({ resume_text: resultText })
        setParsedResume(resp.parsed_resume)
        if (type === 'pdf') setShowPdfPreview(true)
        else setShowHhPreview(true)
      } catch { /* ignore */ }
    } else {
      if (type === 'pdf') setShowPdfPreview(true)
      else setShowHhPreview(true)
    }
  }

  const handleUrlPaste = (url: string) => {
    setVacancyUrl(url)
    // Auto-fill info message
    if (url && url.includes('hh.ru')) {
      setVacancyText(url)
    }
  }

  const isGenerateDisabled = vacancyText.length < 10 || vacancyText.length > MAX_CHARS

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-lg border-b border-slate-800 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => mode === 'result' ? setMode('input') : navigate('/')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-white">
                {t('ideal.title', 'Ideal Resume Generator')}
              </h1>
              <p className="text-sm text-slate-400">
                {mode === 'input'
                  ? t('ideal.subtitle_input', 'Paste a vacancy to generate a perfect resume template')
                  : t('ideal.subtitle_result', 'Generated ideal resume')}
              </p>
            </div>
          </div>
          {mode === 'result' && (
            <div className="flex gap-2">
              {/* Export dropdown */}
              <div className="relative">
                <Button
                  variant="outline"
                  onClick={() => setShowExportDropdown(!showExportDropdown)}
                  className="text-slate-300 border-slate-600 hover:bg-slate-700"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  {t('wizard.step4.export', 'Export')}
                  <ChevronDown className="w-3 h-3 ml-1" />
                </Button>
                {showExportDropdown && (
                  <div className="absolute right-0 mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20">
                    <button
                      onClick={() => handleExport('pdf')}
                      className="w-full px-3 py-2.5 text-sm text-left text-slate-300 hover:bg-slate-700 rounded-t-lg flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      PDF Preview
                    </button>
                    <button
                      onClick={() => handleExport('hh')}
                      className="w-full px-3 py-2.5 text-sm text-left text-slate-300 hover:bg-slate-700 rounded-b-lg flex items-center gap-2"
                    >
                      <FileText className="w-4 h-4" />
                      HH Export
                    </button>
                  </div>
                )}
              </div>
              <Button variant="outline" onClick={handleCopy} className="text-slate-300 border-slate-600 hover:bg-slate-700">
                {copied ? <Check className="w-4 h-4 mr-1" /> : <Copy className="w-4 h-4 mr-1" />}
                {copied ? t('common.copied', 'Copied!') : t('common.copy', 'Copy')}
              </Button>
              <Button onClick={() => setShowSaveDialog(true)} className="bg-blue-600 hover:bg-blue-700">
                <Save className="w-4 h-4 mr-1" />
                {t('common.save', 'Save')}
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {mode === 'input' ? (
          <div className="space-y-6">
            {/* URL input */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
              <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <LinkIcon className="w-4 h-4" />
                {t('ideal.vacancy_url', 'Vacancy URL (hh.ru)')}
              </label>
              <input
                type="url"
                value={vacancyUrl}
                onChange={(e) => handleUrlPaste(e.target.value)}
                placeholder="https://hh.ru/vacancy/..."
                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-2">
                {t('ideal.url_hint', 'Or paste the vacancy text below')}
              </p>
            </div>

            {/* Vacancy text */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
              <TextAreaWithCounter
                value={vacancyText}
                onChange={setVacancyText}
                maxLength={MAX_CHARS}
                label={t('ideal.vacancy_text', 'Vacancy text')}
                placeholder={t('ideal.vacancy_placeholder', `Paste vacancy text here...

For example:
Senior Python Developer
Company XYZ
Requirements:
- 5+ years of Python experience
- FastAPI, PostgreSQL, Docker
...`)}
                minHeight={250}
              />
            </div>

            {/* Options */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
              <button
                onClick={() => setShowOptions(!showOptions)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Settings className="w-5 h-5 text-slate-400" />
                  <span className="font-medium text-white">{t('ideal.settings', 'Generation Settings')}</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${showOptions ? 'rotate-180' : ''}`} />
              </button>
              {showOptions && (
                <div className="px-6 pb-6 space-y-4 border-t border-slate-700 pt-4">
                  <OptionGroup
                    label={t('ideal.language', 'Resume Language')}
                    options={[
                      { value: null, label: t('ideal.auto', 'Auto') },
                      { value: 'ru' as const, label: 'Русский' },
                      { value: 'en' as const, label: 'English' },
                    ]}
                    selected={options.language}
                    onChange={(v) => setOptions(p => ({ ...p, language: v }))}
                  />
                  <OptionGroup
                    label={t('ideal.template', 'Template')}
                    options={[
                      { value: null, label: t('ideal.default', 'Default') },
                      { value: 'harvard' as const, label: 'Harvard' },
                    ]}
                    selected={options.template}
                    onChange={(v) => setOptions(p => ({ ...p, template: v }))}
                  />
                  <OptionGroup
                    label={t('ideal.seniority', 'Experience Level')}
                    options={[
                      { value: null, label: t('ideal.any', 'Any') },
                      { value: 'junior' as const, label: 'Junior' },
                      { value: 'middle' as const, label: 'Middle' },
                      { value: 'senior' as const, label: 'Senior' },
                    ]}
                    selected={options.seniority}
                    onChange={(v) => setOptions(p => ({ ...p, seniority: v }))}
                  />
                </div>
              )}
            </div>

            {/* Error */}
            {generateMutation.isError && (
              <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400">
                {generateMutation.error instanceof Error
                  ? generateMutation.error.message
                  : t('ideal.error', 'Error generating resume')}
              </div>
            )}

            {/* Generate button */}
            <div className="flex justify-center">
              <Button
                onClick={handleGenerate}
                disabled={isGenerateDisabled || generateMutation.isPending}
                className="min-w-[280px] py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    {t('ideal.generating', 'Generating...')}
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    {t('ideal.generate', 'Generate Ideal Resume')}
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Generated Resume */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Resume text — 2/3 */}
              <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="bg-slate-800/50 px-6 py-3 border-b border-slate-700 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <span className="font-semibold text-white">{t('ideal.result_title', 'Ideal Resume')}</span>
                  </div>
                  {generateMutation.data?.cache_hit && (
                    <span className="text-xs text-slate-400 bg-slate-700 px-2 py-1 rounded">cached</span>
                  )}
                </div>
                <div className="max-h-[600px] overflow-y-auto custom-scrollbar p-4 font-mono">
                  <FormattedResumeView text={resultText} />
                </div>
              </div>

              {/* Metadata — 1/3 */}
              <div className="space-y-4">
                {metadata && metadata.keywords_used.length > 0 && (
                  <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                    <h3 className="text-sm font-semibold text-blue-400 mb-3">
                      {t('ideal.ats_keywords', 'ATS Keywords')}
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {metadata.keywords_used.map((kw, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-blue-500/15 text-blue-300 rounded-md border border-blue-500/20">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {metadata && metadata.structure.length > 0 && (
                  <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">
                      {t('ideal.structure', 'Structure')}
                    </h3>
                    <div className="space-y-1">
                      {metadata.structure.map((s, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-slate-400">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          {s}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {metadata && metadata.assumptions.length > 0 && (
                  <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                    <h3 className="text-sm font-semibold text-amber-400 mb-3">
                      {t('ideal.assumptions', 'Assumptions')}
                    </h3>
                    <ul className="space-y-1.5 text-sm text-slate-400">
                      {metadata.assumptions.map((a, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-amber-500 mt-0.5">•</span>
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Back */}
            <div className="flex justify-start">
              <Button variant="outline" onClick={() => setMode('input')} className="text-slate-300 border-slate-600">
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t('ideal.edit_vacancy', 'Edit Vacancy')}
              </Button>
            </div>
          </div>
        )}
      </main>

      {/* Save dialog */}
      <ConfirmDialog
        isOpen={showSaveDialog}
        title={t('ideal.save_title', 'Save Version')}
        message={
          <div className="space-y-3">
            <p>{t('ideal.save_message', 'Save ideal resume to version history?')}</p>
            <input
              type="text"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500"
              placeholder={t('ideal.save_placeholder', 'Version name (optional)')}
              value={versionTitle}
              onChange={(e) => setVersionTitle(e.target.value)}
            />
          </div>
        }
        confirmText={saveVersionMutation.isPending ? t('common.saving', 'Saving...') : t('common.save', 'Save')}
        onConfirm={() => saveVersionMutation.mutate()}
        onClose={() => setShowSaveDialog(false)}
      />

      {/* PDF Preview */}
      {showPdfPreview && parsedResume && (
        <PdfPreview data={parsedResume} onClose={() => setShowPdfPreview(false)} />
      )}

      {/* HH Preview */}
      {showHhPreview && parsedResume && (
        <HeadHunterPreview data={parsedResume} onClose={() => setShowHhPreview(false)} />
      )}
    </div>
  )
}

// ========================================
// Helper Components
// ========================================

function OptionGroup<T>({
  label,
  options,
  selected,
  onChange,
}: {
  label: string
  options: { value: T; label: string }[]
  selected: T
  onChange: (v: T) => void
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      <div className="flex gap-2 flex-wrap">
        {options.map((opt) => (
          <button
            key={opt.label}
            onClick={() => onChange(opt.value)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${selected === opt.value
              ? 'bg-blue-500/20 text-blue-300 border-2 border-blue-500/50'
              : 'bg-slate-900 text-slate-400 border-2 border-transparent hover:bg-slate-700'
              }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function FormattedResumeView({ text }: { text: string }) {
  if (!text) return <p className="text-slate-500 text-sm italic">No content</p>
  const formatted = formatResumeText(text)

  return (
    <>
      {formatted.split('\n').map((line, i) => {
        if (line.trim() === '') return <div key={i} className="h-3" />
        if (SECTION_PATTERN.test(line.trim())) {
          return (
            <div key={i} className="mt-5 mb-1.5 pb-1 border-b border-slate-600">
              <span className="text-xs font-bold uppercase tracking-widest text-blue-400">{line.trim()}</span>
            </div>
          )
        }
        return (
          <div key={i} className={`${line.trim().startsWith('•') ? 'pl-4' : 'pl-3'} py-0.5`}>
            <span className="text-slate-300 text-[13px] leading-relaxed">{line}</span>
          </div>
        )
      })}
    </>
  )
}
