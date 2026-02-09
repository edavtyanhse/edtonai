import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { FileText, Loader2, ArrowRight, ArrowLeft, Edit3, Save, Check, UploadCloud, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { parseResume, updateResume } from '@/api'
import { Button, TextAreaWithCounter } from '@/components'
import ResumeEditor from '@/components/ResumeEditor'
import { extractTextFromFile } from '@/lib/file-processing'
import type { ParsedResume } from '@/api'

const MAX_CHARS = 15000

type Mode = 'input' | 'parsed'

export default function Step1Resume() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { state, setResumeText, setResumeData, updateParsedResume, goToNextStep } = useWizard()
  const [mode, setMode] = useState<Mode>(state.parsedResume ? 'parsed' : 'input')
  const [localText, setLocalText] = useState(state.resumeText)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [isProcessingFile, setIsProcessingFile] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsProcessingFile(true)
    setFileError(null)

    try {
      const text = await extractTextFromFile(file)
      if (text.length < 50) {
        throw new Error(t('common.error')) // Simplification or specific error key
      }
      if (text.length > MAX_CHARS) {
        setLocalText(text.slice(0, MAX_CHARS))
        parseMutation.mutate(text.slice(0, MAX_CHARS))
      } else {
        setLocalText(text)
        parseMutation.mutate(text)
      }
    } catch (err: any) {
      setFileError(err.message || t('common.error'))
    } finally {
      setIsProcessingFile(false)
    }
  }, [t])

  // Parse mutation
  const parseMutation = useMutation({
    mutationFn: (text: string = localText) => parseResume({ resume_text: typeof text === 'string' ? text : localText }),
    onSuccess: (data) => {
      setResumeText(localText)
      setResumeData(data.resume_id, data.parsed_resume)
      setMode('parsed')
      setHasUnsavedChanges(false)
    },
  })

  // Save mutation (separate from navigation)
  const saveMutation = useMutation({
    mutationFn: (parsed: ParsedResume) =>
      updateResume(state.resumeId!, { parsed_data: parsed }),
    onSuccess: (data) => {
      if (data.parsed_data) {
        updateParsedResume(data.parsed_data)
      }
      setHasUnsavedChanges(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    },
  })

  const handleParse = () => {
    parseMutation.mutate(localText)
  }

  const handleEditText = () => {
    setMode('input')
  }

  const handleSave = () => {
    if (state.parsedResume && state.resumeId) {
      saveMutation.mutate(state.parsedResume)
    }
  }

  const handleNext = () => {
    goToNextStep()
  }

  const handleParsedChange = (parsed: ParsedResume) => {
    updateParsedResume(parsed)
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  // Simple Drag & Drop Area
  const FileUploadArea = () => {
    const hasFile = localText.length > 50 // Consider file uploaded if we have substantial text

    return (
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer relative ${hasFile
          ? 'border-green-500/50 bg-green-900/10'
          : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'
          }`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          onDrop(Array.from(e.dataTransfer.files))
        }}
        onClick={() => !hasFile && document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt"
          onChange={(e) => e.target.files && onDrop(Array.from(e.target.files))}
        />

        {isProcessingFile ? (
          <div className="flex flex-col items-center justify-center py-4">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
            <p className="text-sm text-slate-300">{t('wizard.step1.analyzing')}</p>
          </div>
        ) : hasFile ? (
          <div className="flex flex-col items-center justify-center py-4">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-sm font-medium text-white">{t('wizard.step1.file_loaded')}</h3>
            <p className="text-xs text-slate-400 mt-1">
              {localText.length.toLocaleString()} {t('wizard.step1.characters')}
            </p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setLocalText('')
                setFileError(null)
              }}
              className="mt-3 flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              <X className="w-3 h-3" />
              {t('wizard.step1.remove_file')}
            </button>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
              <UploadCloud className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-sm font-medium text-white">{t('wizard.step1.upload_tab')}</h3>
            <p className="text-xs text-slate-400 mt-1">
              {t('wizard.step1.supports')}
            </p>
          </>
        )}

        {fileError && (
          <div className="absolute inset-x-0 bottom-0 p-2 bg-red-900/50 text-red-300 text-xs rounded-b-lg border-t border-red-500/30 flex items-center justify-center">
            <X className="w-3 h-3 mr-1" />
            {fileError}
          </div>
        )}
      </div>
    )
  }


  const isParseDisabled = localText.length < 10 || localText.length > MAX_CHARS

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('wizard.step1.title')}</h1>
          <p className="text-slate-400 mt-1">
            {t('wizard.step1.description')}
          </p>
        </div>
        {mode === 'parsed' && (
          <Button variant="ghost" onClick={handleEditText} className="text-slate-400 hover:text-white">
            <Edit3 className="w-4 h-4 mr-2" />
            {t('common.back_to_step')} 1
          </Button>
        )}
      </div>

      {/* Content */}
      {mode === 'input' ? (
        <div className="space-y-4">

          {/* Include File Upload Area here */}
          <FileUploadArea />

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-2 text-slate-500">{t('wizard.step1.text_tab')}</span>
            </div>
          </div>

          <TextAreaWithCounter
            value={localText}
            onChange={setLocalText}
            maxLength={MAX_CHARS}
            label={t('wizard.steps.resume')}
            placeholder={t('wizard.step1.manual_placeholder')}
            minHeight={300}
          />

          <div className="flex justify-between items-center">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('common.back_to_home')}
            </Button>
            <Button
              onClick={handleParse}
              disabled={isParseDisabled || parseMutation.isPending}
              className="min-w-[180px]"
            >
              {parseMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('wizard.step1.analyzing')}
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  {t('wizard.step1.next')}
                </>
              )}
            </Button>
          </div>

          {parseMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {parseMutation.error instanceof Error
                ? parseMutation.error.message
                : t('common.error')}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {state.parsedResume && (
            <ResumeEditor
              data={state.parsedResume}
              onChange={handleParsedChange}
            />
          )}

          {/* Unsaved changes indicator */}
          {hasUnsavedChanges && (
            <div className="text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
              ⚠ {t('wizard.step4.pending')}
            </div>
          )}

          <div className="flex justify-between gap-3">
            <Button variant="ghost" onClick={handleEditText} className="text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('common.back_to_step')} 1
            </Button>

            <div className="flex gap-3">
              {/* Separate Save button */}
              <Button
                variant="outline"
                onClick={handleSave}
                disabled={!hasUnsavedChanges || saveMutation.isPending}
                className="min-w-[150px]"
              >
                {saveMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : saveSuccess ? (
                  <>
                    <Check className="w-4 h-4 mr-2 text-green-600" />
                    {t('common.success')}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {t('common.save')}
                  </>
                )}
              </Button>

              {/* Next button (navigation only) */}
              <Button
                onClick={handleNext}
                className="min-w-[150px]"
              >
                {t('wizard.step1.next')}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Cache indicator */}
      {parseMutation.data?.cache_hit && (
        <div className="text-sm text-gray-500 bg-gray-50 px-3 py-2 rounded-lg">
          ✓ {t('common.success')} (Cache)
        </div>
      )}
    </div>
  )
}
