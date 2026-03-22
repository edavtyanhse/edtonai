import { useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { BarChart2, Loader2, ArrowRight, ArrowLeft, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { analyzeMatch } from '@/api'
import type { Gap } from '@/api'
import { Button } from '@/components'

export default function Step3Analysis() {
  const { t } = useTranslation()
  const { state, setAnalysis, goToNextStep, goToPrevStep } = useWizard()

  // Analyze mutation (context-aware if improvements were previously applied)
  const analyzeMutation = useMutation({
    mutationFn: () => {
      const hasContext = state.appliedCheckboxIds.length > 0 && state.analysis
      return analyzeMatch({
        resume_text: state.resumeText,
        vacancy_text: state.vacancyText,
        ...(hasContext ? {
          original_analysis: state.analysis!,
          applied_checkbox_ids: state.appliedCheckboxIds,
        } : {}),
      })
    },
    onSuccess: (data) => {
      setAnalysis(data.analysis_id, data.analysis)
    },
  })

  // Auto-trigger analysis on mount if not already analyzed
  useEffect(() => {
    if (!state.analysis && !analyzeMutation.isPending && !analyzeMutation.isError) {
      analyzeMutation.mutate()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const analysis = state.analysis
  const hasAnalysis = !!analysis
  const isLoading = analyzeMutation.isPending

  // Show loading state while analyzing
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 min-h-[400px] space-y-6">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full" />
          <Loader2 className="w-16 h-16 text-blue-500 animate-spin relative z-10" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-medium text-white">
            {t('wizard.step1.analyzing')}
          </h3>
          <p className="text-yellow-400 max-w-md mx-auto text-sm">
            ⏳ {t('wizard.step3.analyzing_warning')}
          </p>
        </div>
        <Button variant="ghost" onClick={goToPrevStep} className="text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('common.back_to_step')} 2
        </Button>
      </div>
    )
  }

  // Show error state
  if (analyzeMutation.isError && !hasAnalysis) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('wizard.steps.analysis')}</h1>
          <p className="text-slate-400 mt-1">{t('wizard.step3.description')}</p>
        </div>
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300">
          {analyzeMutation.error instanceof Error
            ? analyzeMutation.error.message
            : t('common.error')}
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={goToPrevStep} className="text-slate-400 hover:text-white">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back_to_step')} 2
          </Button>
          <Button onClick={() => analyzeMutation.mutate()}>
            <BarChart2 className="w-4 h-4 mr-2" />
            {t('wizard.step2.analyze_button')}
          </Button>
        </div>
      </div>
    )
  }

  // Show analysis results (skip the intermediate "preview cards" screen)
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">{t('wizard.steps.analysis')}</h1>
        <p className="text-slate-400 mt-1">{t('wizard.step3.description')}</p>
      </div>

      {hasAnalysis && (
        <div className="space-y-6">

          {/* Score */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{t('wizard.step3.score')}</h2>
              <div className="flex items-center gap-3">
                {state.previousScore !== null && state.previousScore !== analysis.score && (
                  <div className="text-2xl text-slate-500 line-through">
                    {state.previousScore}
                  </div>
                )}
                <div
                  className={`text-4xl font-bold ${analysis.score >= 70
                    ? 'text-green-600'
                    : analysis.score >= 50
                      ? 'text-yellow-600'
                      : 'text-red-600'
                    }`}
                >
                  {analysis.score}
                  <span className="text-lg text-gray-400">/100</span>
                </div>
                {state.previousScore !== null && analysis.score > state.previousScore && (
                  <span className="text-sm font-medium text-green-400 bg-green-900/30 px-2 py-1 rounded">
                    +{analysis.score - state.previousScore}
                  </span>
                )}
              </div>
            </div>

            {/* Score breakdown */}
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
                  label="Четкость"
                  value={analysis.score_breakdown.clarity_evidence.value}
                  maxValue={10}
                  comment={analysis.score_breakdown.clarity_evidence.comment}
                />
              )}
            </div>
          </div>

          {/* Skills match */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Required skills */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="font-medium text-white mb-3">{t('wizard.step3.required_skills')}</h3>
              <div className="space-y-2">
                {analysis.matched_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis.missing_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis.matched_required_skills.length === 0 &&
                  analysis.missing_required_skills.length === 0 && (
                    <p className="text-sm text-gray-500">{t('wizard.step3.no_data')}</p>
                  )}
              </div>
            </div>

            {/* Preferred skills */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="font-medium text-white mb-3">{t('wizard.step3.preferred_skills')}</h3>
              <div className="space-y-2">
                {analysis.matched_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis.missing_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis.matched_preferred_skills.length === 0 &&
                  analysis.missing_preferred_skills.length === 0 && (
                    <p className="text-sm text-gray-500">{t('wizard.step3.no_data')}</p>
                  )}
              </div>
            </div>
          </div>

          {/* Gaps */}
          {analysis.gaps.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="font-medium text-white mb-3">
                {t('wizard.step3.gaps')} ({analysis.gaps.length})
              </h3>
              <div className="space-y-3">
                {analysis.gaps.map((gap: Gap) => (
                  <div
                    key={gap.id}
                    className={`p-3 rounded-lg border ${gap.severity === 'high'
                      ? 'bg-red-900/20 border-red-500/30'
                      : gap.severity === 'medium'
                        ? 'bg-yellow-900/20 border-yellow-500/30'
                        : 'bg-blue-900/20 border-blue-500/30'
                      }`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle
                        className={`w-4 h-4 mt-0.5 ${gap.severity === 'high'
                          ? 'text-red-400'
                          : gap.severity === 'medium'
                            ? 'text-yellow-400'
                            : 'text-blue-400'
                          }`}
                      />
                      <div>
                        <p className="text-sm font-medium text-white">{gap.message}</p>
                        {gap.suggestion && (
                          <p className="text-sm text-slate-300 mt-1">{gap.suggestion}</p>
                        )}
                        <span className="inline-block mt-1 text-xs text-slate-500">
                          {gap.target_section}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="ghost" onClick={goToPrevStep} className="text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('common.back_to_step')} 2
            </Button>
            <Button onClick={goToNextStep} className="min-w-[150px]">
              {t('wizard.step3.improve_button')}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>

          {/* Cache indicator */}
          {analyzeMutation.data?.cache_hit && (
            <div className="text-sm text-gray-500 bg-gray-50 px-3 py-2 rounded-lg">
              ✓ {t('common.success')} (Cache)
            </div>
          )}
        </div>
      )}
    </div>
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
    <div className="bg-slate-700 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-300">{label}</span>
        <span className="text-sm font-medium text-white">
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

function SkillBadge({ skill, matched }: { skill: string; matched: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${matched ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}
    >
      {matched ? (
        <CheckCircle className="w-4 h-4 text-green-500" />
      ) : (
        <XCircle className="w-4 h-4 text-red-500" />
      )}
      {skill}
    </div>
  )
}
