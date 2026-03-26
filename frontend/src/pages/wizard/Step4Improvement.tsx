import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, Loader2, ArrowLeft, RotateCcw, Check, X, CheckCircle, XCircle, TrendingUp, TrendingDown, Minus, Eye, Home, Mail, ChevronDown, Briefcase, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { adaptResume, createVersion, analyzeMatch, generateCoverLetter, parseResume } from '@/api'
import type { CheckboxOption, CoverLetterResponse } from '@/api'
import { Button, CheckboxList, ConfirmDialog, CoverLetterModal, HeadHunterPreview } from '@/components'
import PdfPreview from '@/components/pdf/PdfPreview'
import type { ChangeLogEntry, SelectedImprovement } from '@/api'
import { trackBehaviorEvent } from '@/features/feedback/analytics'
// FEEDBACK FEATURE - remove these imports to disable
import { FeedbackModal, useFeedback } from '@/features/feedback'

type Mode = 'checkboxes' | 'review' | 'analysis'

interface PendingChange extends ChangeLogEntry {
  status: 'pending' | 'confirmed' | 'rejected'
}

import { diffWords } from 'diff'

export default function Step4Improvement() {
  const { t } = useTranslation()
  const {
    state,
    setSelectedCheckboxes,
    setResult,
    setAnalysis,
    applyImprovedResume,
    goToPrevStep,
    reset,
    updateParsedResume,
  } = useWizard()
  const [mode, setMode] = useState<Mode>(state.resultText ? 'review' : 'checkboxes')
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showPdfPreview, setShowPdfPreview] = useState(false)
  const [isPreparingPdf, setIsPreparingPdf] = useState(false)
  const [versionTitle, setVersionTitle] = useState('')
  const [pendingChanges, setPendingChanges] = useState<PendingChange[]>([])
  const [lastAppliedChanges, setLastAppliedChanges] = useState<ChangeLogEntry[]>([])
  const [showCoverLetterModal, setShowCoverLetterModal] = useState(false)
  const [coverLetterData, setCoverLetterData] = useState<CoverLetterResponse | null>(null)
  const [showExportDropdown, setShowExportDropdown] = useState(false)
  const [showHhPreview, setShowHhPreview] = useState(false)
  const [currentVersionId, setCurrentVersionId] = useState<string | null>(null)
  const [navigateAfterFeedback, setNavigateAfterFeedback] = useState(false)
  // FEEDBACK FEATURE - remove this hook to disable
  const feedback = useFeedback()

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowExportDropdown(false)
        setShowPdfPreview(false)
        setShowHhPreview(false)
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [])

  // User inputs for checkboxes that require_user_input
  const [userInputs, setUserInputs] = useState<Record<string, string>>({})
  // AI generate flags for checkboxes that require_user_input
  const [aiGenerateFlags, setAiGenerateFlags] = useState<Record<string, boolean>>({})

  const checkboxOptions = state.analysis?.checkbox_options || []

  // Build selected_improvements from checkboxes + user inputs
  const buildSelectedImprovements = (): SelectedImprovement[] => {
    return state.selectedCheckboxes.map((checkboxId: string) => {
      const option = checkboxOptions.find((o: CheckboxOption) => o.id === checkboxId)
      const userInput = userInputs[checkboxId]
      const aiGenerate = aiGenerateFlags[checkboxId] || false

      return {
        checkbox_id: checkboxId,
        user_input: userInput || null,
        ai_generate: option?.requires_user_input ? (aiGenerate || !userInput) : false,
      }
    })
  }

  // Adapt mutation
  const adaptMutation = useMutation({
    mutationFn: () =>
      adaptResume({
        resume_text: state.resumeText,
        vacancy_text: state.vacancyText,
        selected_improvements: buildSelectedImprovements(),
      }),
    onSuccess: (data) => {
      setResult(data.updated_resume_text, data.change_log)
      setCurrentVersionId(data.version_id)
      // Initialize pending changes for review
      setPendingChanges(
        data.change_log.map((entry) => ({
          ...entry,
          status: 'pending' as const,
        }))
      )
      setMode('review')
    },
  })

  // Re-analyze mutation - runs automatically after confirming
  const reanalyzeMutation = useMutation({
    mutationFn: async (newResumeText: string) => {
      const analysisPromise = analyzeMatch({
        resume_text: newResumeText,
        vacancy_text: state.vacancyText,
      }).catch(e => {
        console.error('Analysis failed:', e)
        return null
      })

      const parsePromise = parseResume({
        resume_text: newResumeText,
      }).catch(e => {
        console.error('Parse resume failed:', e)
        return null
      })

      const [analysisData, parseData] = await Promise.all([analysisPromise, parsePromise])
      return { analysisData, parseData }
    },
    onSuccess: (data) => {
      if (data.analysisData) {
        setAnalysis(data.analysisData.analysis_id, data.analysisData.analysis)
      }
      // Update parsed resume data so PDF preview reflects the changes
      if (data.parseData?.parsed_resume) {
        updateParsedResume(data.parseData.parsed_resume)
      }
    },
    onSettled: () => {
      setMode('analysis')
    },
  })

  // Cover letter mutation
  const coverLetterMutation = useMutation({
    mutationFn: () =>
      generateCoverLetter({
        resume_version_id: currentVersionId!,
      }),
    onSuccess: (data) => {
      setCoverLetterData(data)
      setShowCoverLetterModal(true)
    },
  })

  // Save version mutation
  const saveVersionMutation = useMutation({
    mutationFn: (resumeText: string) =>
      createVersion({
        type: 'adapt',
        title: versionTitle || undefined,
        resume_text: state.resumeText,
        vacancy_text: state.vacancyText,
        result_text: resumeText,
        selected_checkbox_ids: state.selectedCheckboxes,
        analysis_id: state.analysisId || undefined,
      }),
    onSuccess: (data, resumeText) => {
      setShowSaveDialog(false)
      setVersionTitle('')
      // Update version ID so cover letter uses the improved resume
      if (data?.id) setCurrentVersionId(data.id)

      // Save the changes we just applied to show them in the UI
      // Filter only confirmed or pending (effectively confirmed) changes
      const applied = pendingChanges.filter(c => c.status !== 'rejected')
      setLastAppliedChanges(applied)

      // Apply improved resume as new base
      applyImprovedResume(resumeText)
      // Run re-analysis with new text
      reanalyzeMutation.mutate(resumeText)
    },
    onError: (error, resumeText) => {
      console.error('Failed to save version, but proceeding to analysis', error)
      setShowSaveDialog(false)

      const applied = pendingChanges.filter(c => c.status !== 'rejected')
      setLastAppliedChanges(applied)

      applyImprovedResume(resumeText)
      reanalyzeMutation.mutate(resumeText)
    },
  })

  const handleApply = () => {
    adaptMutation.mutate()
  }

  const handleConfirmChange = (index: number) => {
    setPendingChanges((prev) =>
      prev.map((change, i) =>
        i === index ? { ...change, status: 'confirmed' as const } : change
      )
    )
  }

  const handleRejectChange = (index: number) => {
    setPendingChanges((prev) =>
      prev.map((change, i) =>
        i === index ? { ...change, status: 'rejected' as const } : change
      )
    )
  }

  const handleConfirmAll = () => {
    setPendingChanges((prev) =>
      prev.map((change) => ({ ...change, status: 'confirmed' as const }))
    )
  }

  const handleFinalizeChanges = () => {
    setShowSaveDialog(true)
  }

  const handleGenerateCoverLetter = () => {
    if (!currentVersionId) return
    coverLetterMutation.mutate()
  }

  const handleOpenPdfPreview = async () => {
    setShowExportDropdown(false)
    trackBehaviorEvent('export_clicked', {
      step: 'step_4',
      properties: {
        export_type: 'pdf_preview',
      },
    })

    if (state.parsedResume) {
      setShowPdfPreview(true)
      return
    }

    setIsPreparingPdf(true)
    try {
      const parseData = await parseResume({
        resume_text: state.resumeText,
      })
      updateParsedResume(parseData.parsed_resume)
      setShowPdfPreview(true)
    } catch (error) {
      console.error('Failed to prepare PDF preview:', error)
    } finally {
      setIsPreparingPdf(false)
    }
  }

  const handleOpenHhPreview = async () => {
    setShowExportDropdown(false)
    if (state.parsedResume) {
      setShowHhPreview(true)
      return
    }

    setIsPreparingPdf(true)
    try {
      const parseData = await parseResume({
        resume_text: state.resumeText,
      })
      updateParsedResume(parseData.parsed_resume)
      setShowHhPreview(true)
    } catch (error) {
      console.error('Failed to prepare HH preview:', error)
    } finally {
      setIsPreparingPdf(false)
    }
  }

  const handleSaveAndAnalyze = () => {
    saveVersionMutation.mutate(state.resultText)
  }

  const handleBackToCheckboxes = () => {
    setMode('checkboxes')
    setPendingChanges([])
  }

  const handleSelectAll = () => {
    // Select all options (enabled field is deprecated, now all options are enabled)
    const allIds = checkboxOptions.map((o: CheckboxOption) => o.id)
    setSelectedCheckboxes(allIds)
  }

  const handleDeselectAll = () => {
    setSelectedCheckboxes([])
  }

  const handleContinueImproving = () => {
    // Go back to checkbox selection for more improvements
    setMode('checkboxes')
  }

  const selectedCount = state.selectedCheckboxes.length
  // Count total options (enabled field is deprecated)
  const totalCount = checkboxOptions.length
  const pendingCount = pendingChanges.filter((c) => c.status === 'pending').length
  const confirmedCount = pendingChanges.filter((c) => c.status === 'confirmed').length
  const allReviewed = pendingChanges.length > 0 && pendingCount === 0

  const analysis = state.analysis
  const scoreDiff = state.previousScore !== null && analysis
    ? analysis.score - state.previousScore
    : null

  const isProcessing = saveVersionMutation.isPending || reanalyzeMutation.isPending

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-20 min-h-[400px] space-y-6">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full" />
          <Loader2 className="w-16 h-16 text-blue-500 animate-spin relative z-10" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-medium text-white">
            {saveVersionMutation.isPending ? t('wizard.step4.applying') : t('wizard.step1.analyzing')}
          </h3>
          <p className="text-yellow-400 max-w-md mx-auto text-sm">
            ⏳ {t('wizard.step4.applying_warning')}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {mode === 'analysis' ? t('wizard.step4.result_title') : t('wizard.step4.title')}
          </h1>
          <p className="text-gray-500 mt-1">
            {mode === 'checkboxes'
              ? t('wizard.step4.description')
              : mode === 'review'
                ? t('wizard.step4.result_description')
                : t('wizard.step3.description')}
          </p>
        </div>
        {mode === 'analysis' && (
          <div className="flex gap-2" role="toolbar" aria-label={t('wizard.step4.actions', 'Действия с результатом')}>
            <div className="relative">
              <span id="export-dropdown-trigger" className="hidden">Export Dropdown</span>
              <Button
                onClick={() => setShowExportDropdown(!showExportDropdown)}
                disabled={isPreparingPdf || reanalyzeMutation.isPending}
                className="bg-slate-700 hover:bg-slate-600 border-slate-600"
                aria-haspopup="true"
                aria-expanded={showExportDropdown}
                aria-controls="export-menu"
              >
                {isPreparingPdf ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Eye className="w-4 h-4 mr-2" />
                )}
                {t('common.export', 'Экспорт')}
                <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showExportDropdown ? 'rotate-180' : ''}`} />
              </Button>

              {showExportDropdown && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowExportDropdown(false)}
                  />
                  <div
                    id="export-menu"
                    role="menu"
                    aria-labelledby="export-dropdown-trigger"
                    className="absolute right-0 mt-2 w-56 bg-slate-800 rounded-lg shadow-xl border border-slate-700 z-20 py-1 overflow-hidden focus:outline-none"
                  >
                    <button
                      className="w-full flex items-center px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 transition-colors gap-3 focus:bg-slate-700 focus:outline-none"
                      onClick={handleOpenPdfPreview}
                      role="menuitem"
                    >
                      <FileText className="w-4 h-4 text-red-400" />
                      <div className="text-left">
                        <div className="font-semibold">{t('wizard.step4.preview_pdf', 'PDF Формат')}</div>
                        <div className="text-xs text-slate-400">{t('wizard.step4.pdf_desc', 'Для печати и отправки почтой')}</div>
                      </div>
                    </button>
                    <button
                      className="w-full flex items-center px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 transition-colors gap-3 border-t border-slate-700 focus:bg-slate-700 focus:outline-none"
                      onClick={handleOpenHhPreview}
                      role="menuitem"
                    >
                      <Briefcase className="w-4 h-4 text-blue-400" />
                      <div className="text-left">
                        <div className="font-semibold">{t('wizard.step4.hh_export', 'HeadHunter')}</div>
                        <div className="text-xs text-slate-400">{t('wizard.step4.hh_export_desc', 'Копирование блоков для hh.ru')}</div>
                      </div>
                    </button>
                  </div>
                </>
              )}
            </div>
            <Button
              onClick={handleGenerateCoverLetter}
              disabled={!currentVersionId || coverLetterMutation.isPending}
            >
              {coverLetterMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Mail className="w-4 h-4 mr-2" />
              )}
              {t('wizard.step4.generate_cover_letter')}
            </Button>
          </div>
        )}
      </div>

      {mode === 'checkboxes' ? (
        <div className="space-y-4">
          {/* Selection controls */}
          <div className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-lg p-3">
            <span className="text-sm text-slate-300">
              {t('wizard.step4.selected')}: {selectedCount} / {totalCount}
            </span>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                {t('wizard.step4.select_all')}
              </Button>
              <Button variant="ghost" size="sm" onClick={handleDeselectAll}>
                {t('wizard.step4.deselect_all')}
              </Button>
            </div>
          </div>

          {/* Checkbox list */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg">
            <CheckboxList
              options={checkboxOptions}
              selected={state.selectedCheckboxes}
              onChange={setSelectedCheckboxes}
              userInputs={userInputs}
              onUserInputChange={(id, value) => setUserInputs((prev) => ({ ...prev, [id]: value }))}
              aiGenerateFlags={aiGenerateFlags}
              onAiGenerateChange={(id, value) => setAiGenerateFlags((prev) => ({ ...prev, [id]: value }))}
            />
          </div>

          {adaptMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {adaptMutation.error instanceof Error
                ? adaptMutation.error.message
                : 'Ошибка при улучшении резюме'}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="ghost" onClick={goToPrevStep} className="text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('common.back_to_step')} 3
            </Button>
            <Button
              onClick={handleApply}
              disabled={selectedCount === 0 || adaptMutation.isPending}
              className="min-w-[200px]"
            >
              {adaptMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('wizard.step4.applying')}
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  {t('wizard.step4.apply_button')} ({selectedCount})
                </>
              )}
            </Button>
          </div>
        </div>
      ) : mode === 'review' ? (
        <div className="space-y-4">
          {/* Review status */}
          <div className="flex items-center justify-between bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
            <span className="text-sm text-blue-300">
              {t('wizard.step4.confirmed')}: {confirmedCount} / {pendingChanges.length}
              {pendingCount > 0 && ` • ${t('wizard.step4.pending')}: ${pendingCount}`}
            </span>
            <Button variant="ghost" size="sm" onClick={handleConfirmAll} disabled={pendingCount === 0}>
              <Check className="w-4 h-4 mr-1" />
              {t('wizard.step4.confirm_all')}
            </Button>
          </div>

          {/* Change review cards */}
          <div className="space-y-3">
            <h3 className="font-medium text-white">{t('wizard.step4.changes_review')}</h3>
            {pendingChanges.map((change, index) => (
              <div
                key={index}
                className={`bg-slate-800 border rounded-lg p-4 transition-colors ${change.status === 'confirmed'
                  ? 'border-green-500/30 bg-green-900/20'
                  : change.status === 'rejected'
                    ? 'border-red-500/30 bg-red-900/20 opacity-60'
                    : 'border-slate-700'
                  }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                        {change.where}
                      </span>
                      {change.status === 'confirmed' && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                          ✓ {t('wizard.step4.change_confirmed')}
                        </span>
                      )}
                      {change.status === 'rejected' && (
                        <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">
                          ✗ {t('wizard.step4.change_rejected')}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-white">{change.what_changed}</p>
                    {change.before_excerpt && (
                      <div className="mt-2 text-xs">
                        <span className="text-gray-500">{t('wizard.step4.before')} </span>
                        <span className="text-red-600 line-through">{change.before_excerpt}</span>
                      </div>
                    )}
                    {change.after_excerpt && (
                      <div className="mt-1 text-xs">
                        <span className="text-gray-500">{t('wizard.step4.after')} </span>
                        <span className="text-green-600">{change.after_excerpt}</span>
                      </div>
                    )}
                  </div>
                  {change.status === 'pending' && (
                    <div className="flex gap-2 flex-shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleConfirmChange(index)}
                        className="text-green-600 border-green-300 hover:bg-green-50"
                      >
                        <Check className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRejectChange(index)}
                        className="text-red-600 border-red-300 hover:bg-red-50"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="flex justify-between pt-4">
            <Button variant="ghost" onClick={handleBackToCheckboxes} className="text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('wizard.step4.back_edit')}
            </Button>
            <Button
              onClick={handleFinalizeChanges}
              disabled={!allReviewed || confirmedCount === 0}
              className="min-w-[200px]"
            >
              <Check className="w-4 h-4 mr-2" />
              {t('wizard.step4.apply_final')} ({confirmedCount})
            </Button>
          </div>
        </div>
      ) : (
        /* mode === 'analysis' - Full analysis view */
        <div className="space-y-6">

          {/* 1. Score Panel - Full Width with ScoreCard bars */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{t('wizard.step4.score_new')}</h2>
              <div className="flex items-center gap-4">
                {state.previousScore !== null && scoreDiff !== null && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">{t('wizard.step4.before')}: {state.previousScore}</span>
                    <span className="text-gray-400">→</span>
                    {scoreDiff > 0 ? (
                      <span className="flex items-center text-green-500">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        +{scoreDiff}
                      </span>
                    ) : scoreDiff < 0 ? (
                      <span className="flex items-center text-red-500">
                        <TrendingDown className="w-4 h-4 mr-1" />
                        {scoreDiff}
                      </span>
                    ) : (
                      <span className="flex items-center text-gray-500">
                        <Minus className="w-4 h-4 mr-1" />
                        0
                      </span>
                    )}
                  </div>
                )}
                <div className={`text-4xl font-bold ${analysis && analysis.score >= 70 ? 'text-green-500' : analysis && analysis.score >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
                  {analysis?.score || 0}
                  <span className="text-lg text-gray-400">/100</span>
                </div>
              </div>
            </div>
            {/* Horizontal Score breakdown with progress bars */}
            {analysis && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {analysis.score_breakdown.skill_fit && (
                  <ScoreCard
                    label={t('wizard.step3.score_skills')}
                    value={analysis.score_breakdown.skill_fit.value}
                    maxValue={50}
                    comment={analysis.score_breakdown.skill_fit.comment}
                  />
                )}
                {analysis.score_breakdown.experience_fit && (
                  <ScoreCard
                    label={t('wizard.step3.score_experience')}
                    value={analysis.score_breakdown.experience_fit.value}
                    maxValue={25}
                    comment={analysis.score_breakdown.experience_fit.comment}
                  />
                )}
                {analysis.score_breakdown.ats_fit && (
                  <ScoreCard
                    label={t('wizard.step3.score_ats')}
                    value={analysis.score_breakdown.ats_fit.value}
                    maxValue={15}
                    comment={analysis.score_breakdown.ats_fit.comment}
                  />
                )}
                {analysis.score_breakdown.clarity_evidence && (
                  <ScoreCard
                    label={t('wizard.step3.score_clarity')}
                    value={analysis.score_breakdown.clarity_evidence.value}
                    maxValue={10}
                    comment={analysis.score_breakdown.clarity_evidence.comment}
                  />
                )}
              </div>
            )}
          </div>

          {/* 2. Split View: Resume Diff (2/3) + Improvements (1/3) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Resume Diff */}
            <div className="lg:col-span-2">
              <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-blue-400" />
                {state.previousResumeText
                  ? t('wizard.step4.optimization_result')
                  : t('wizard.step4.current_resume')
                }
              </h3>
              <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                <ResumeDiffViewer
                  oldText={state.previousResumeText || state.resumeText}
                  newText={state.resumeText}
                />
              </div>
            </div>

            {/* Right: Improvements List */}
            <div className="space-y-4">
              {/* Improvements - what got better */}
              {lastAppliedChanges.length > 0 && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <h3 className="font-medium text-green-400 mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    {t('wizard.step3.improvements')}
                  </h3>
                  {lastAppliedChanges.length > 0 ? (
                    <div className="space-y-2">
                      {lastAppliedChanges.map((change, idx) => (
                        <div key={idx} className="flex gap-2 text-sm text-green-200">
                          <Check className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                          <span>{change.what_changed}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-green-300/70 italic">{t('wizard.step4.general_improvements')}</p>
                  )}
                </div>
              )}

              {/* Hint to continue improving */}
              {analysis && analysis.checkbox_options.length > 0 && (
                <div className="bg-blue-900/15 border border-blue-500/20 rounded-lg p-4">
                  <p className="text-sm text-blue-300/80">
                    <Sparkles className="w-3.5 h-3.5 inline-block mr-1.5 text-blue-400" />
                    {t('wizard.step4.continue_hint')}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* 3. Skills Section - Side by Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Required skills */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
              <h3 className="font-medium text-white mb-4 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-blue-400" />
                {t('wizard.step3.required_skills')}
              </h3>
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {analysis?.matched_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis?.missing_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis?.matched_required_skills.length === 0 && analysis?.missing_required_skills.length === 0 && (
                  <p className="text-sm text-gray-500">{t('wizard.step3.no_data')}</p>
                )}
              </div>
            </div>

            {/* Preferred skills */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
              <h3 className="font-medium text-white mb-4 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-500" />
                {t('wizard.step3.preferred_skills')}
              </h3>
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {analysis?.matched_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis?.missing_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis?.matched_preferred_skills.length === 0 && analysis?.missing_preferred_skills.length === 0 && (
                  <p className="text-sm text-gray-400 italic">{t('wizard.step3.no_data')}</p>
                )}
              </div>
            </div>
          </div>

          {/* 4. Actions Footer */}
          <div className="flex justify-between items-center pt-6 border-t border-slate-800">
            <div className="flex gap-2">
              <Button variant="outline" onClick={reset} className="text-slate-400 hover:text-white border-slate-700 hover:bg-slate-800">
                <RotateCcw className="w-4 h-4 mr-2" />
                {t('wizard.step4.start_over')}
              </Button>
            </div>
            <div className="flex gap-3">
              {analysis && analysis.checkbox_options.length > 0 && (
                <Button onClick={handleContinueImproving} className="bg-blue-600 hover:bg-blue-700">
                  <Sparkles className="w-4 h-4 mr-2" />
                  {t('wizard.step4.continue')}
                </Button>
              )}
              <Button
                onClick={() => feedback.showFeedback('result')}
                className="bg-emerald-700 hover:bg-emerald-600"
              >
                {t('wizard.step4.rate_result', 'Оценить результат')}
              </Button>
              <Button
                onClick={() => {
                  const shown = feedback.showFeedbackAuto()
                  if (shown) {
                    setNavigateAfterFeedback(true)
                  } else {
                    window.location.href = '/'
                  }
                }}
                className="bg-slate-700 hover:bg-slate-600"
              >
                <Home className="w-4 h-4 mr-2" />
                {t('common.done')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* PDF Preview Dialog (in Analysis mode) - Keeping it here or moving out? 
                Analysis mode has its own button for PDF. But let's check review mode.
                Review mode doesn't have PDF button. Checkboxes mode doesn't.
                So PDF preview is irrelevant for others? 
                Wait, user might want to see it?
                Actually, let's keep it global if possible, but the button is only in Analysis.
                However, ConfirmDialog MUST be global as it's triggered from Review mode.
            */}


      {/* Save dialog - Global */}
      <ConfirmDialog
        isOpen={showSaveDialog}
        title={t('wizard.step4.apply_final')}
        message={
          <p className="text-slate-300">
            {t('wizard.step4.final_confirm_message', 'Apply confirmed changes? The updated resume will become the base for further improvements.')}
          </p>
        }
        confirmText={saveVersionMutation.isPending || reanalyzeMutation.isPending ? t('wizard.step4.applying') : t('wizard.step4.apply_final')}
        onConfirm={handleSaveAndAnalyze}
        onClose={() => setShowSaveDialog(false)}
      />

      {/* PDF Preview Dialog - Global */}
      {
        showPdfPreview && state.parsedResume && (
          <PdfPreview
            data={state.parsedResume}
            onClose={() => setShowPdfPreview(false)}
          />
        )
      }

      {/* HeadHunter Preview Modal - Global */}
      {
        showHhPreview && state.parsedResume && (
          <HeadHunterPreview
            data={state.parsedResume}
            onClose={() => setShowHhPreview(false)}
          />
        )
      }

      {/* Cover Letter Modal */}
      {showCoverLetterModal && coverLetterData && (
        <CoverLetterModal
          isOpen={showCoverLetterModal}
          onClose={() => setShowCoverLetterModal(false)}
          coverLetter={coverLetterData.cover_letter_text}
          structure={coverLetterData.structure}
          keyPoints={coverLetterData.key_points_used}
          alignmentNotes={coverLetterData.alignment_notes}
        />
      )}

      {/* FEEDBACK FEATURE - remove this modal to disable auto-popup after analysis */}
      {feedback.isEnabled && (
        <FeedbackModal
          isOpen={feedback.isOpen}
          onClose={() => {
            feedback.closeFeedback()
            if (navigateAfterFeedback) {
              window.location.href = '/'
            }
          }}
          source={feedback.source}
        />
      )}
    </div >
  )
}
// ========================================
// Helper Components
// ========================================

function ScoreCard({
  label,
  value,
  maxValue,
  comment,
}: {
  label: string
  value: number
  maxValue: number
  comment: string
}) {
  const percentage = (value / maxValue) * 100

  return (
    <div className="bg-slate-800 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-400">{label}</span>
        <span className="text-sm font-medium">
          {value}/{maxValue}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${percentage >= 70 ? 'bg-green-500' : percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {comment && <p className="text-xs text-gray-500 mt-1 truncate" title={comment}>{comment}</p>}
    </div>
  )
}

// Format raw resume text (from API) into readable lines with section breaks
function formatResumeText(text: string): string {
  if (!text) return ''

  // Section keywords to detect
  const sections = [
    'EDUCATION', 'EXPERIENCE', 'WORK EXPERIENCE', 'SKILLS', 'SKILLS & LANGUAGES',
    'SUMMARY', 'SUMMARY:', 'ABOUT', 'CONTACT', 'CONTACTS', 'PERSONAL',
    'PROJECTS', 'CERTIFICATIONS', 'LANGUAGES', 'AWARDS', 'PUBLICATIONS',
    'INTERESTS', 'OBJECTIVE',
    'ПРОФИЛЬ', 'ОПЫТ', 'ОПЫТ РАБОТЫ', 'ОБРАЗОВАНИЕ', 'НАВЫКИ',
    'ПРОЕКТЫ', 'СЕРТИФИКАТЫ', 'ЯЗЫКИ', 'О СЕБЕ', 'КОНТАКТЫ', 'ДОСТИЖЕНИЯ'
  ]

  let formatted = text

  // Insert line breaks before section headers
  for (const section of sections) {
    // Match section preceded by space/pipe/start, case-insensitive
    const regex = new RegExp(`(\\s*\\|?\\s*)(${section.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&')})(?=\\s)`, 'gi')
    formatted = formatted.replace(regex, '\n\n$2')
  }

  // Insert line breaks before bullet points
  formatted = formatted.replace(/\s*•\s*/g, '\n• ')

  // Insert line breaks before date-like company entries (e.g. "CompanyName   Месяц 20XX")
  formatted = formatted.replace(/\s{2,}((?:Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})/gi, '\n$1')

  // Insert line break before "Languages:" and "Technical Skills:"
  formatted = formatted.replace(/\s+(Languages:|Technical Skills:)/g, '\n$1')

  // Clean up: collapse multiple blank lines, trim
  formatted = formatted.replace(/\n{3,}/g, '\n\n').trim()

  return formatted
}

function ResumeDiffViewer({ oldText, newText }: { oldText: string, newText: string }) {
  // Format both texts before comparing
  const formattedOld = formatResumeText(oldText)
  const formattedNew = formatResumeText(newText)
  const hasDiff = formattedOld !== formattedNew

  // Section heading patterns for visual styling
  const sectionPattern = /^(EDUCATION|EXPERIENCE|WORK EXPERIENCE|SKILLS|SKILLS & LANGUAGES|SUMMARY:?|ABOUT|CONTACT|CONTACTS|PERSONAL|PROJECTS|CERTIFICATIONS|LANGUAGES|AWARDS|PUBLICATIONS|INTERESTS|OBJECTIVE|ПРОФИЛЬ|ОПЫТ|ОПЫТ РАБОТЫ|ОБРАЗОВАНИЕ|НАВЫКИ|ПРОЕКТЫ|СЕРТИФИКАТЫ|ЯЗЫКИ|О СЕБЕ|КОНТАКТЫ|ДОСТИЖЕНИЯ)\s*$/i

  const isSectionHeading = (line: string) => sectionPattern.test(line.trim())

  // Render formatted text without diff (no previous version)
  if (!hasDiff) {
    const lines = formattedNew.split('\n')
    return (
      <div className="bg-slate-900 p-4 overflow-auto max-h-[600px] custom-scrollbar font-mono">
        {lines.map((line, i) => {
          if (line.trim() === '') return <div key={i} className="h-3" />
          if (isSectionHeading(line)) {
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

  // Word-level diff for precise highlighting
  const diffs = diffWords(formattedOld, formattedNew)

  // Build an array of styled segments, then split by newlines for rendering
  type Segment = { text: string; type: 'added' | 'removed' | 'unchanged' }
  const allSegments: Segment[] = []

  diffs.forEach((part) => {
    const type = part.added ? 'added' as const : part.removed ? 'removed' as const : 'unchanged' as const
    allSegments.push({ text: part.value, type })
  })

  // Now render: split segments by newline to create visual lines
  // Each "visual line" is an array of segments
  type LineSegment = { text: string; type: 'added' | 'removed' | 'unchanged' }
  const lines: LineSegment[][] = [[]]

  allSegments.forEach(seg => {
    const parts = seg.text.split('\n')
    parts.forEach((part, idx) => {
      if (idx > 0) {
        // New line
        lines.push([])
      }
      if (part !== '') {
        lines[lines.length - 1].push({ text: part, type: seg.type })
      }
    })
  })

  const hasChanges = (segments: LineSegment[]) =>
    segments.some(s => s.type === 'added' || s.type === 'removed')

  return (
    <div className="bg-slate-900 p-4 overflow-auto max-h-[600px] custom-scrollbar font-mono">
      {lines.map((lineSegments, lineIdx) => {
        // Empty line
        if (lineSegments.length === 0) return <div key={lineIdx} className="h-3" />

        const fullText = lineSegments.map(s => s.text).join('')

        // Section heading
        if (isSectionHeading(fullText)) {
          const hasAdded = lineSegments.some(s => s.type === 'added')
          const hasRemoved = lineSegments.some(s => s.type === 'removed')
          return (
            <div key={lineIdx} className={`mt-5 mb-1.5 pb-1 border-b border-slate-600 ${hasAdded ? 'border-green-500/40' : hasRemoved ? 'border-red-500/40' : ''
              }`}>
              <span className={`text-xs font-bold uppercase tracking-widest ${hasAdded ? 'text-green-400' : hasRemoved ? 'text-red-400' : 'text-blue-400'
                }`}>
                {fullText.trim()}
              </span>
            </div>
          )
        }

        const isBullet = fullText.trim().startsWith('•')
        const lineChanged = hasChanges(lineSegments)

        return (
          <div
            key={lineIdx}
            className={`${isBullet ? 'pl-4' : 'pl-3'} py-0.5 my-0.5 ${lineChanged ? 'border-l-3 border-blue-500/50 bg-blue-900/10 rounded-r' : ''
              }`}
          >
            {lineSegments.map((seg, segIdx) => {
              if (seg.type === 'added') {
                return (
                  <span key={segIdx} className="bg-green-800/50 text-green-300 text-[13px] leading-relaxed px-0.5 rounded">
                    {seg.text}
                  </span>
                )
              }
              if (seg.type === 'removed') {
                return (
                  <span key={segIdx} className="bg-red-800/40 text-red-400 line-through text-[13px] leading-relaxed px-0.5 rounded opacity-70">
                    {seg.text}
                  </span>
                )
              }
              return (
                <span key={segIdx} className="text-slate-400 text-[13px] leading-relaxed">
                  {seg.text}
                </span>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}

function SkillBadge({ skill, matched }: { skill: string; matched: boolean }) {
  return (
    <div
      className={`px-3 py-2 rounded-lg border flex items-center gap-2 ${matched
        ? 'bg-green-900/20 border-green-500/30 text-green-200'
        : 'bg-red-900/20 border-red-500/30 text-red-200'
        }`}
    >
      {matched ? (
        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
      ) : (
        <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
      )}
      <span className="text-sm font-medium">{skill}</span>
    </div>
  )
}
