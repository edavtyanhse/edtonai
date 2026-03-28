import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Trash2, Eye, RotateCcw, FileText, Sparkles, Calendar, ArrowLeft,
  Check, CheckCircle, XCircle, Download, ChevronDown
} from 'lucide-react'
import { diffWords } from 'diff'
import { Button, ConfirmDialog, HeadHunterPreview } from '@/components'
import PdfPreview from '@/components/pdf/PdfPreview'
import {
  getVersions, getVersion, deleteVersion, parseResume,
  type VersionItem, type VersionDetail, type ChangeLogEntry, type ParsedResume
} from '@/api'

export default function History() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(
    searchParams.get('view')
  )
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const {
    data: versionsData,
    isLoading: isLoadingList,
    error: listError,
  } = useQuery({
    queryKey: ['versions'],
    queryFn: () => getVersions(50, 0),
  })

  const {
    data: selectedVersion,
    isLoading: isLoadingDetail,
  } = useQuery({
    queryKey: ['version', selectedVersionId],
    queryFn: () => getVersion(selectedVersionId!),
    enabled: !!selectedVersionId,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteVersion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      if (selectedVersionId === deleteConfirm) setSelectedVersionId(null)
      setDeleteConfirm(null)
    },
  })

  const handleRestore = (version: VersionDetail) => {
    navigate('/', {
      state: {
        restoreVersion: {
          resumeText: version.resume_text || '',
          vacancyText: version.vacancy_text,
          resultText: version.result_text,
        },
      },
    })
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  }

  const versions = versionsData?.items || []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/')} className="text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back', 'Back')}
        </Button>
        <h1 className="text-2xl font-bold text-white">{t('history.title', 'Version History')}</h1>
      </div>

      {listError && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          Failed to load versions: {(listError as Error).message}
        </div>
      )}

      {isLoadingList ? (
        <div className="text-center py-12 text-slate-400">Loading...</div>
      ) : versions.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 mb-4">{t('history.empty', 'No saved versions yet')}</p>
          <Button onClick={() => navigate('/')}>{t('history.create_first', 'Create your first version')}</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Version list */}
          <div className="lg:col-span-1 space-y-2 max-h-[80vh] overflow-y-auto custom-scrollbar pr-1">
            {versions.map((version: VersionItem) => (
              <div
                key={version.id}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedVersionId === version.id
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                  }`}
                onClick={() => setSelectedVersionId(version.id)}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-sm font-medium text-white">
                      {version.title || t('history.adapted_resume', 'Adapted Resume')}
                    </span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 uppercase">
                    {version.type}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <Calendar className="w-3 h-3" />
                  {formatDate(version.created_at)}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteConfirm(version.id) }}
                  className="text-xs text-red-500/60 hover:text-red-400 flex items-center gap-1 mt-2"
                >
                  <Trash2 className="w-3 h-3" />
                  {t('common.delete', 'Delete')}
                </button>
              </div>
            ))}
          </div>

          {/* Version detail */}
          <div className="lg:col-span-3">
            {selectedVersionId ? (
              isLoadingDetail ? (
                <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center text-slate-400">Loading...</div>
              ) : selectedVersion ? (
                <VersionDetailView
                  version={selectedVersion}
                  onRestore={() => handleRestore(selectedVersion)}
                  formatDate={formatDate}
                />
              ) : null
            ) : (
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-12 text-center">
                <Eye className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                <p className="text-slate-400">{t('history.select_version', 'Select a version to view details')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        title={t('history.delete_title', 'Delete Version')}
        message={t('history.delete_message', 'Are you sure you want to delete this version? This action cannot be undone.')}
        confirmText={t('common.delete', 'Delete')}
        variant="danger"
      />
    </div>
  )
}

// ========================================
// Version Detail View (mirrors Step4 analysis mode)
// ========================================

function VersionDetailView({
  version,
  onRestore,
  formatDate,
}: {
  version: VersionDetail
  onRestore: () => void
  formatDate: (d: string) => string
}) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'result' | 'resume' | 'vacancy'>('result')
  const [showPdfPreview, setShowPdfPreview] = useState(false)
  const [showHhPreview, setShowHhPreview] = useState(false)
  const [showExportDropdown, setShowExportDropdown] = useState(false)
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)

  // Parse result_text for previews
  const handleExport = async (type: 'pdf' | 'hh') => {
    setShowExportDropdown(false)
    if (!parsedResume && version.result_text) {
      try {
        const resp = await parseResume({ resume_text: version.result_text })
        setParsedResume(resp.parsed_resume)
        if (type === 'pdf') setShowPdfPreview(true)
        else setShowHhPreview(true)
      } catch { /* ignore */ }
    } else {
      if (type === 'pdf') setShowPdfPreview(true)
      else setShowHhPreview(true)
    }
  }

  const changes = version.change_log || []
  const hasChanges = changes.length > 0
  const hasDiff = version.resume_text && version.result_text && version.resume_text !== version.result_text

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">
              {version.title || t('history.adapted_resume', 'Adapted Resume')}
            </h2>
            <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(version.created_at)}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-400 uppercase">
                {version.type}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Export dropdown */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowExportDropdown(!showExportDropdown)}
                className="text-slate-300 border-slate-600 hover:bg-slate-700"
              >
                <Eye className="w-4 h-4 mr-1" />
                {t('wizard.step4.export', 'Export')}
                <ChevronDown className="w-3 h-3 ml-1" />
              </Button>
              {showExportDropdown && (
                <div className="absolute right-0 mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
                  <button
                    onClick={() => handleExport('pdf')}
                    className="w-full px-3 py-2 text-sm text-left text-slate-300 hover:bg-slate-700 rounded-t-lg flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    PDF Preview
                  </button>
                  <button
                    onClick={() => handleExport('hh')}
                    className="w-full px-3 py-2 text-sm text-left text-slate-300 hover:bg-slate-700 rounded-b-lg flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    HH Export
                  </button>
                </div>
              )}
            </div>
            <Button size="sm" onClick={onRestore} className="bg-blue-600 hover:bg-blue-700">
              <RotateCcw className="w-4 h-4 mr-1" />
              {t('history.restore', 'Restore')}
            </Button>
          </div>
        </div>
      </div>

      {/* What Improved */}
      {hasChanges && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            {t('wizard.step4.what_improved', 'What Improved')}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {changes.map((change: ChangeLogEntry, idx: number) => (
              <div key={idx} className="flex items-start gap-2 text-sm bg-green-900/10 border border-green-500/20 rounded-lg p-2.5">
                <Check className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                <span className="text-green-200">{change.what_changed}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="flex border-b border-slate-700">
          {(['result', 'resume', 'vacancy'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/5'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
            >
              {tab === 'result' ? t('history.tab_result', 'Optimized Resume')
                : tab === 'resume' ? t('history.tab_original', 'Original Resume')
                  : t('history.tab_vacancy', 'Vacancy')}
            </button>
          ))}
        </div>

        <div className="max-h-[600px] overflow-auto custom-scrollbar">
          {activeTab === 'result' && hasDiff ? (
            <ResumeDiffViewer oldText={version.resume_text} newText={version.result_text} />
          ) : (
            <div className="p-4">
              <FormattedText text={
                activeTab === 'result' ? version.result_text
                  : activeTab === 'resume' ? version.resume_text
                    : version.vacancy_text
              } />
            </div>
          )}
        </div>
      </div>

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
// Shared Components (mirrored from Step4)
// ========================================

function formatResumeText(text: string): string {
  if (!text) return ''
  const sections = [
    'EDUCATION', 'EXPERIENCE', 'WORK EXPERIENCE', 'SKILLS', 'SKILLS & LANGUAGES',
    'SUMMARY', 'SUMMARY:', 'ABOUT', 'CONTACT', 'CONTACTS', 'PERSONAL',
    'PROJECTS', 'CERTIFICATIONS', 'LANGUAGES', 'AWARDS', 'PUBLICATIONS',
    'INTERESTS', 'OBJECTIVE',
    'ПРОФИЛЬ', 'ОПЫТ', 'ОПЫТ РАБОТЫ', 'ОБРАЗОВАНИЕ', 'НАВЫКИ',
    'ПРОЕКТЫ', 'СЕРТИФИКАТЫ', 'ЯЗЫКИ', 'О СЕБЕ', 'КОНТАКТЫ', 'ДОСТИЖЕНИЯ'
  ]
  let formatted = text
  for (const section of sections) {
    const regex = new RegExp(`(\\s*\\|?\\s*)(${section.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?=\\s)`, 'gi')
    formatted = formatted.replace(regex, '\n\n$2')
  }
  formatted = formatted.replace(/\s*•\s*/g, '\n• ')
  formatted = formatted.replace(/\s{2,}((?:January|February|March|April|May|June|July|August|September|October|November|December|Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь)\s+\d{4})/gi, '\n$1')
  formatted = formatted.replace(/\s+(Languages:|Technical Skills:)/g, '\n$1')
  formatted = formatted.replace(/\n{3,}/g, '\n\n').trim()
  return formatted
}

function FormattedText({ text }: { text: string }) {
  if (!text) return <p className="text-slate-500 text-sm italic">No content</p>
  const formatted = formatResumeText(text)
  const sectionPattern = /^(EDUCATION|EXPERIENCE|WORK EXPERIENCE|SKILLS|SKILLS & LANGUAGES|SUMMARY:?|ABOUT|PROJECTS|CERTIFICATIONS|LANGUAGES|ПРОФИЛЬ|ОПЫТ|ОПЫТ РАБОТЫ|ОБРАЗОВАНИЕ|НАВЫКИ|ПРОЕКТЫ|СЕРТИФИКАТЫ|ЯЗЫКИ|О СЕБЕ|КОНТАКТЫ|ДОСТИЖЕНИЯ)\s*$/i

  return (
    <div className="font-mono">
      {formatted.split('\n').map((line, i) => {
        if (line.trim() === '') return <div key={i} className="h-3" />
        if (sectionPattern.test(line.trim())) {
          return (
            <div key={i} className="mt-5 mb-1.5 pb-1 border-b border-slate-600">
              <span className="text-xs font-bold uppercase tracking-widest text-blue-400">{line.trim()}</span>
            </div>
          )
        }
        return (
          <div key={i} className={`${line.trim().startsWith('•') ? 'pl-4' : 'pl-3'} py-0.5`}>
            <span className="text-slate-400 text-[13px] leading-relaxed">{line}</span>
          </div>
        )
      })}
    </div>
  )
}

function ResumeDiffViewer({ oldText, newText }: { oldText: string; newText: string }) {
  const formattedOld = formatResumeText(oldText)
  const formattedNew = formatResumeText(newText)
  const sectionPattern = /^(EDUCATION|EXPERIENCE|WORK EXPERIENCE|SKILLS|SKILLS & LANGUAGES|SUMMARY:?|ABOUT|PROJECTS|CERTIFICATIONS|LANGUAGES|ПРОФИЛЬ|ОПЫТ|ОПЫТ РАБОТЫ|ОБРАЗОВАНИЕ|НАВЫКИ|ПРОЕКТЫ|СЕРТИФИКАТЫ|ЯЗЫКИ|О СЕБЕ|КОНТАКТЫ|ДОСТИЖЕНИЯ)\s*$/i
  const isSectionHeading = (line: string) => sectionPattern.test(line.trim())

  const diffs = diffWords(formattedOld, formattedNew)

  type Segment = { text: string; type: 'added' | 'removed' | 'unchanged' }
  const allSegments: Segment[] = diffs.map(part => ({
    text: part.value,
    type: part.added ? 'added' : part.removed ? 'removed' : 'unchanged',
  }))

  type LineSegment = { text: string; type: 'added' | 'removed' | 'unchanged' }
  const lines: LineSegment[][] = [[]]
  allSegments.forEach(seg => {
    const parts = seg.text.split('\n')
    parts.forEach((part, idx) => {
      if (idx > 0) lines.push([])
      if (part !== '') lines[lines.length - 1].push({ text: part, type: seg.type })
    })
  })

  const hasChanges = (segments: LineSegment[]) =>
    segments.some(s => s.type === 'added' || s.type === 'removed')

  return (
    <div className="p-4 font-mono">
      {lines.map((lineSegments, lineIdx) => {
        if (lineSegments.length === 0) return <div key={lineIdx} className="h-3" />
        const fullText = lineSegments.map(s => s.text).join('')

        if (isSectionHeading(fullText)) {
          return (
            <div key={lineIdx} className="mt-5 mb-1.5 pb-1 border-b border-slate-600">
              <span className="text-xs font-bold uppercase tracking-widest text-blue-400">{fullText.trim()}</span>
            </div>
          )
        }

        const isBullet = fullText.trim().startsWith('•')
        const lineChanged = hasChanges(lineSegments)

        return (
          <div
            key={lineIdx}
            className={`${isBullet ? 'pl-4' : 'pl-3'} py-0.5 my-0.5 ${lineChanged ? 'border-l-3 border-blue-500/50 bg-blue-900/10 rounded-r' : ''}`}
          >
            {lineSegments.map((seg, segIdx) => {
              if (seg.type === 'added') {
                return <span key={segIdx} className="bg-green-800/50 text-green-300 text-[13px] leading-relaxed px-0.5 rounded">{seg.text}</span>
              }
              if (seg.type === 'removed') {
                return <span key={segIdx} className="bg-red-800/40 text-red-400 line-through text-[13px] leading-relaxed px-0.5 rounded opacity-70">{seg.text}</span>
              }
              return <span key={segIdx} className="text-slate-400 text-[13px] leading-relaxed">{seg.text}</span>
            })}
          </div>
        )
      })}
    </div>
  )
}
