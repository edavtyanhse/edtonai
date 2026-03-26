import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Briefcase, Loader2, ArrowRight, ArrowLeft, Save, Check, Link as LinkIcon, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { parseVacancy, updateVacancy } from '@/api'
import { Button, TextAreaWithCounter } from '@/components'
import VacancyEditor from '@/components/VacancyEditor'
import type { ParsedVacancy } from '@/api'
import { trackBehaviorEvent } from '@/features/feedback/analytics'

const MAX_CHARS = 10000

type Mode = 'input' | 'parsed'

export default function Step2Vacancy() {
  const { t } = useTranslation()
  const {
    state,
    setVacancyText,
    setVacancyData,
    updateParsedVacancy,
    clearVacancy,
    goToNextStep,
    goToPrevStep,
  } = useWizard()
  const [mode, setMode] = useState<Mode>(state.parsedVacancy ? 'parsed' : 'input')
  const [localText, setLocalText] = useState(state.vacancyText)
  const [url, setUrl] = useState('')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Parse mutation
  const parseMutation = useMutation({
    mutationFn: () => parseVacancy({ vacancy_text: localText, url: url || undefined }),
    onSuccess: (data) => {
      setVacancyText(data.raw_text)
      setLocalText(data.raw_text)
      setVacancyData(data.vacancy_id, data.parsed_vacancy)
      setMode('parsed')
      setHasUnsavedChanges(false)
      trackBehaviorEvent('vacancy_added', {
        step: 'step_2',
        properties: {
          vacancy_id: data.vacancy_id,
          cache_hit: data.cache_hit,
          has_source_url: Boolean(url),
        },
      })
    },
  })

  // Save mutation (separate from navigation)
  const saveMutation = useMutation({
    mutationFn: (parsed: ParsedVacancy) =>
      updateVacancy(state.vacancyId!, { parsed_data: parsed }),
    onSuccess: (data) => {
      if (data.parsed_data) {
        updateParsedVacancy(data.parsed_data)
      }
      setHasUnsavedChanges(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    },
  })

  const handleParse = () => {
    if (!localText && !url) return
    parseMutation.mutate()
  }

  const handleChangeVacancy = () => {
    clearVacancy()
    setLocalText('')
    setUrl('')
    setMode('input')
  }

  const handleSave = () => {
    if (state.parsedVacancy && state.vacancyId) {
      saveMutation.mutate(state.parsedVacancy)
    }
  }

  const handleNext = () => {
    goToNextStep()
  }

  const handleParsedChange = (parsed: ParsedVacancy) => {
    updateParsedVacancy(parsed)
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const isParseDisabled = (!localText && !url) || (localText.length > 0 && (localText.length < 10 || localText.length > MAX_CHARS))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('wizard.steps.vacancy')}</h1>
          <p className="text-gray-500 mt-1">
            {mode === 'input'
              ? t('wizard.step2.description')
              : t('wizard.step2.description')}
          </p>
        </div>
        {mode === 'parsed' && (
          <Button variant="ghost" onClick={handleChangeVacancy} className="text-slate-400 hover:text-white">
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('wizard.step2.change_vacancy')}
          </Button>
        )}
      </div>

      {/* Content */}
      {mode === 'input' ? (
        <div className="space-y-6">

          {/* URL Input */}
          <div className="bg-slate-800 p-4 border border-slate-700 rounded-lg shadow-sm">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              {t('wizard.step2.import_url')}
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LinkIcon className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="url"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-600 rounded-md leading-5 bg-slate-900 text-white placeholder-slate-500 focus:outline-none focus:placeholder-slate-400 focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                  placeholder="https://hh.ru/vacancy/..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
                  disabled={localText.length > 0}
                />
              </div>
            </div>
            {localText.length > 0 && (
              <p className="text-xs text-orange-400 mt-2">
                * {t('wizard.step2.url_disabled_hint')}
              </p>
            )}
          </div>

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
            onChange={(val) => {
              setLocalText(val)
              if (val.length > 0) setUrl('') // Clear URL if text is entered
            }}
            maxLength={MAX_CHARS}
            label={t('wizard.step2.description')}
            placeholder={t('wizard.step2.placeholder')}
            minHeight={300}
          />

          <div className="flex justify-between">
            <Button variant="outline" onClick={goToPrevStep}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('wizard.step2.back')}
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
                  <Briefcase className="w-4 h-4 mr-2" />
                  {t('wizard.step2.analyze_button')}
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
          {state.parsedVacancy && (
            <VacancyEditor
              data={state.parsedVacancy}
              onChange={handleParsedChange}
            />
          )}

          <div className="flex justify-between">
            <div className="flex gap-3">
              <Button variant="outline" onClick={goToPrevStep}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t('wizard.step2.back')}
              </Button>
              <Button variant="ghost" onClick={handleChangeVacancy} className="text-slate-400 hover:text-white">
                <RefreshCw className="w-4 h-4 mr-2" />
                {t('wizard.step2.change_vacancy')}
              </Button>
            </div>
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
                    {t('common.save') || 'Save'}
                  </>
                )}
              </Button>

              {/* Next button (navigation only) */}
              <Button
                onClick={handleNext}
                className="min-w-[150px]"
              >
                {t('wizard.step2.next')}
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
