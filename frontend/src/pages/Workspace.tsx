import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { Copy, Save, Sparkles, FileText, X, Eye, AlertCircle, Mail } from 'lucide-react'
import { Button, TextAreaWithCounter, DiffViewer, CheckboxList, ConfirmDialog, CoverLetterModal } from '@/components'
import {
  analyzeMatch,
  adaptResume,
  generateIdeal,
  generateCoverLetter,
  getLimits,
  createVersion,
  type CheckboxOption,
  type LimitsResponse,
  type CoverLetterResponse,
} from '@/api'
import { saveDraft, loadDraft, debounce } from '@/utils'

// Default limits fallback
const DEFAULT_LIMITS: LimitsResponse = {
  max_resume_chars: 15000,
  max_vacancy_chars: 10000,
}

type WorkspaceMode = 'input' | 'analysis' | 'result'

interface RestoreVersionState {
  restoreVersion?: {
    resumeText: string
    vacancyText: string
    resultText: string
  }
}

export default function Workspace() {
  const location = useLocation()
  // Form state
  const [resumeText, setResumeText] = useState('')
  const [vacancyText, setVacancyText] = useState('')
  const [resultText, setResultText] = useState('')
  const [originalResumeText, setOriginalResumeText] = useState('')

  // UI state
  const [mode, setMode] = useState<WorkspaceMode>('input')
  const [showDiff, setShowDiff] = useState(false)
  const [selectedCheckboxes, setSelectedCheckboxes] = useState<string[]>([])
  const [checkboxOptions, setCheckboxOptions] = useState<CheckboxOption[]>([])
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [versionTitle, setVersionTitle] = useState('')
  const [operationType, setOperationType] = useState<'adapt' | 'ideal'>('adapt')
  const [currentVersionId, setCurrentVersionId] = useState<string | null>(null)
  const [showCoverLetterModal, setShowCoverLetterModal] = useState(false)
  const [coverLetterData, setCoverLetterData] = useState<CoverLetterResponse | null>(null)

  // Abort controller for canceling requests
  const abortControllerRef = useRef<AbortController | null>(null)

  // Load limits
  const { data: limits = DEFAULT_LIMITS } = useQuery({
    queryKey: ['limits'],
    queryFn: () => getLimits(),
    staleTime: Infinity,
  })

  // Load draft on mount
  useEffect(() => {
    const draft = loadDraft()
    if (draft) {
      setResumeText(draft.resumeText)
      setVacancyText(draft.vacancyText)
      setResultText(draft.resultText)
    }
  }, [])

  // Handle restored version passed via navigation state
  useEffect(() => {
    const restoreState = location.state as RestoreVersionState | null
    const data = restoreState?.restoreVersion
    if (!data) {
      return
    }

    setResumeText(data.resumeText || '')
    setVacancyText(data.vacancyText || '')
    setResultText(data.resultText || '')
    if (data.resultText) {
      setOriginalResumeText(data.resumeText || '')
      setMode('result')
    }
  }, [location.state])

  // Auto-save draft (debounced)
  const debouncedSaveDraft = useMemo(
    () => debounce(() => saveDraft({ resumeText, vacancyText, resultText }), 1000),
    [resumeText, vacancyText, resultText]
  )

  useEffect(() => {
    debouncedSaveDraft()
  }, [debouncedSaveDraft])

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: (signal: AbortSignal) =>
      analyzeMatch({ resume_text: resumeText, vacancy_text: vacancyText }, signal),
    onSuccess: (data) => {
      setCheckboxOptions(data.analysis.checkbox_options)
      // Pre-select high priority enabled options
      const preSelected = data.analysis.checkbox_options
        .filter((o) => o.enabled && (o.priority ?? 0) >= 2)
        .map((o) => o.id)
      setSelectedCheckboxes(preSelected)
      setMode('analysis')
    },
  })

  // Adapt mutation
  const adaptMutation = useMutation({
    mutationFn: (signal: AbortSignal) =>
      adaptResume(
        {
          resume_text: resumeText,
          vacancy_text: vacancyText,
          selected_checkbox_ids: selectedCheckboxes,
        },
        signal
      ),
    onSuccess: (data) => {
      setResultText(data.updated_resume_text)
      setOriginalResumeText(resumeText)
      setOperationType('adapt')
      setCurrentVersionId(data.version_id) // Save version_id for cover letter
      setMode('result')
    },
  })

  // Ideal mutation
  const idealMutation = useMutation({
    mutationFn: (signal: AbortSignal) =>
      generateIdeal({ vacancy_text: vacancyText }, signal),
    onSuccess: (data) => {
      setResultText(data.ideal_resume_text)
      setOriginalResumeText('')
      setOperationType('ideal')
      setCurrentVersionId(null) // Ideal doesn't create version
      setMode('result')
    },
  })

  // Save version mutation
  const saveVersionMutation = useMutation({
    mutationFn: () =>
      createVersion({
        type: operationType,
        title: versionTitle || undefined,
        resume_text: resumeText || '',
        vacancy_text: vacancyText,
        result_text: resultText,
        selected_checkbox_ids: operationType === 'adapt' ? selectedCheckboxes : undefined,
      }),
    onSuccess: () => {
      setShowSaveDialog(false)
      setVersionTitle('')
      alert('Version saved successfully!')
    },
  })

  // Cover letter mutation
  const coverLetterMutation = useMutation({
    mutationFn: (signal: AbortSignal) =>
      generateCoverLetter({ resume_version_id: currentVersionId! }, signal),
    onSuccess: (data) => {
      setCoverLetterData(data)
      setShowCoverLetterModal(true)
    },
  })

  // Cancel current request
  const cancelRequest = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
  }, [])

  // Handle analyze
  const handleAnalyze = useCallback(() => {
    cancelRequest()
    const controller = new AbortController()
    abortControllerRef.current = controller
    analyzeMutation.mutate(controller.signal)
  }, [analyzeMutation, cancelRequest])

  // Handle adapt
  const handleAdapt = useCallback(() => {
    if (selectedCheckboxes.length === 0) {
      alert('Please select at least one improvement')
      return
    }
    cancelRequest()
    const controller = new AbortController()
    abortControllerRef.current = controller
    adaptMutation.mutate(controller.signal)
  }, [adaptMutation, cancelRequest, selectedCheckboxes])

  // Handle ideal
  const handleIdeal = useCallback(() => {
    cancelRequest()
    const controller = new AbortController()
    abortControllerRef.current = controller
    idealMutation.mutate(controller.signal)
  }, [idealMutation, cancelRequest])

  // Copy result to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(resultText)
      alert('Copied to clipboard!')
    } catch {
      alert('Failed to copy')
    }
  }, [resultText])

  // Reset to input mode
  const handleReset = useCallback(() => {
    setMode('input')
    setResultText('')
    setCheckboxOptions([])
    setSelectedCheckboxes([])
    setShowDiff(false)
    setCurrentVersionId(null)
    setCoverLetterData(null)
  }, [])

  // Handle cover letter generation
  const handleGenerateCoverLetter = useCallback(() => {
    if (!currentVersionId) {
      alert('No version ID available')
      return
    }
    const controller = new AbortController()
    coverLetterMutation.mutate(controller.signal)
  }, [currentVersionId, coverLetterMutation])

  // Validation
  const canAnalyze = resumeText.length >= 10 && vacancyText.length >= 10
  const canIdeal = vacancyText.length >= 10
  const isLoading = analyzeMutation.isPending || adaptMutation.isPending || idealMutation.isPending
  const error = analyzeMutation.error || adaptMutation.error || idealMutation.error

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Resume Workspace</h1>
        {mode !== 'input' && (
          <Button variant="ghost" onClick={handleReset} icon={<X className="w-4 h-4" />}>
            Start Over
          </Button>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{(error as Error).message}</span>
        </div>
      )}

      {/* Main content */}
      {mode === 'input' && (
        <div className="grid grid-cols-2 gap-6">
          {/* Resume input */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <TextAreaWithCounter
              label="Resume Text"
              value={resumeText}
              onChange={setResumeText}
              placeholder="Paste your resume text here..."
              maxLength={limits.max_resume_chars}
              minHeight={400}
            />
          </div>

          {/* Vacancy input */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <TextAreaWithCounter
              label="Vacancy Text"
              value={vacancyText}
              onChange={setVacancyText}
              placeholder="Paste the job description here..."
              maxLength={limits.max_vacancy_chars}
              minHeight={400}
            />
          </div>
        </div>
      )}

      {mode === 'analysis' && (
        <div className="grid grid-cols-3 gap-6">
          {/* Resume preview */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Resume</h3>
            <div className="h-[400px] overflow-auto">
              <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono">
                {resumeText}
              </pre>
            </div>
          </div>

          {/* Checkbox options */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Select Improvements to Apply
            </h3>
            <div className="h-[400px] overflow-auto">
              <CheckboxList
                options={checkboxOptions}
                selected={selectedCheckboxes}
                onChange={setSelectedCheckboxes}
              />
            </div>
          </div>

          {/* Vacancy preview */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Vacancy</h3>
            <div className="h-[400px] overflow-auto">
              <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono">
                {vacancyText}
              </pre>
            </div>
          </div>
        </div>
      )}

      {mode === 'result' && (
        <div className="space-y-4">
          {/* Toggle diff view */}
          {operationType === 'adapt' && originalResumeText && (
            <div className="flex items-center gap-2">
              <Button
                variant={showDiff ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setShowDiff(!showDiff)}
                icon={<Eye className="w-4 h-4" />}
              >
                {showDiff ? 'Hide Changes' : 'Show Changes'}
              </Button>
            </div>
          )}

          {showDiff && originalResumeText ? (
            <div className="bg-white rounded-xl border border-gray-200 p-4 h-[500px]">
              <DiffViewer before={originalResumeText} after={resultText} />
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <TextAreaWithCounter
                label="Result"
                value={resultText}
                onChange={() => {}}
                maxLength={100000}
                minHeight={400}
                readOnly
              />
            </div>
          )}
        </div>
      )}

      {/* Action bar */}
      <div className="flex items-center justify-between bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          {mode === 'input' && (
            <>
              <Button
                onClick={handleAnalyze}
                disabled={!canAnalyze || isLoading}
                loading={analyzeMutation.isPending}
                icon={<Sparkles className="w-4 h-4" />}
              >
                Analyze & Adapt
              </Button>
              <Button
                variant="secondary"
                onClick={handleIdeal}
                disabled={!canIdeal || isLoading}
                loading={idealMutation.isPending}
                icon={<FileText className="w-4 h-4" />}
              >
                Generate Ideal Resume
              </Button>
            </>
          )}

          {mode === 'analysis' && (
            <Button
              onClick={handleAdapt}
              disabled={selectedCheckboxes.length === 0 || isLoading}
              loading={adaptMutation.isPending}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Apply {selectedCheckboxes.length} Improvement
              {selectedCheckboxes.length !== 1 ? 's' : ''}
            </Button>
          )}

          {mode === 'result' && (
            <>
              <Button onClick={handleCopy} variant="secondary" icon={<Copy className="w-4 h-4" />}>
                Copy Result
              </Button>
              {currentVersionId && operationType === 'adapt' && (
                <Button
                  onClick={handleGenerateCoverLetter}
                  variant="secondary"
                  icon={<Mail className="w-4 h-4" />}
                  loading={coverLetterMutation.isPending}
                  disabled={coverLetterMutation.isPending}
                >
                  Cover Letter
                </Button>
              )}
              <Button
                onClick={() => setShowSaveDialog(true)}
                icon={<Save className="w-4 h-4" />}
              >
                Save Version
              </Button>
            </>
          )}
        </div>

        {isLoading && (
          <Button variant="ghost" onClick={cancelRequest}>
            Cancel
          </Button>
        )}
      </div>

      {/* Save dialog */}
      <ConfirmDialog
        isOpen={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        onConfirm={() => saveVersionMutation.mutate()}
        title="Save Version"
        message={
          <div className="space-y-3">
            <p>Save this result as a new version?</p>
            <input
              type="text"
              value={versionTitle}
              onChange={(e) => setVersionTitle(e.target.value)}
              placeholder="Version title (optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        }
        confirmText="Save"
        variant="primary"
      />

      {/* Cover Letter Modal */}
      <CoverLetterModal
        isOpen={showCoverLetterModal}
        onClose={() => setShowCoverLetterModal(false)}
        coverLetter={coverLetterData?.cover_letter_text || ''}
        structure={coverLetterData?.structure}
        keyPoints={coverLetterData?.key_points_used}
        alignmentNotes={coverLetterData?.alignment_notes}
        isLoading={coverLetterMutation.isPending}
      />
    </div>
  )
}
