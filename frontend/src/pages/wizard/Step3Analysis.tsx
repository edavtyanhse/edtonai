import { useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  BarChart2,
  Loader2,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { analyzeMatch } from '@/api'
import type { Gap } from '@/api'
import { Button } from '@/components'
import { trackBehaviorEvent } from '@/features/feedback/analytics'

function getSeverityCardClass(severity: string): string {
  if (severity === 'high') {
    return 'bg-app-danger-soft/70 border-app-danger/35 border-l-4 border-l-app-danger'
  }

  if (severity === 'medium') {
    return 'bg-app-warning-soft/70 border-app-warning/35 border-l-4 border-l-app-warning'
  }

  return 'bg-app-accent-soft/70 border-app-accent/35 border-l-4 border-l-app-accent'
}

function getSeverityIconClass(severity: string): string {
  if (severity === 'high') return 'text-app-danger'
  if (severity === 'medium') return 'text-app-warning'
  return 'text-app-accent'
}

function getSeverityBadgeClass(severity: string): string {
  if (severity === 'high') return 'bg-app-danger-soft text-app-danger'
  if (severity === 'medium') {
    return 'bg-app-warning-soft text-app-warning'
  }
  return 'bg-app-accent-soft text-app-accent'
}

export default function Step3Analysis() {
  const { t } = useTranslation()
  const { state, setAnalysis, goToNextStep, goToPrevStep } = useWizard()

  // Analyze mutation (context-aware if improvements were previously applied)
  const analyzeMutation = useMutation({
    mutationFn: () => {
      trackBehaviorEvent('analysis_started', {
        step: 'step_3',
      })

      const hasContext = state.appliedCheckboxIds.length > 0 && state.analysis
      return analyzeMatch({
        resume_text: state.resumeText,
        vacancy_text: state.vacancyText,
        ...(hasContext
          ? {
              original_analysis: state.analysis!,
              applied_checkbox_ids: state.appliedCheckboxIds,
            }
          : {}),
      })
    },
    onSuccess: (data) => {
      setAnalysis(data.analysis_id, data.analysis)
      trackBehaviorEvent('analysis_finished', {
        step: 'step_3',
        properties: {
          analysis_id: data.analysis_id,
          score: data.analysis.score,
          cache_hit: data.cache_hit,
        },
      })
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
          <h3 className="text-xl font-medium text-app-text">{t('wizard.step1.analyzing')}</h3>
          <p className="text-yellow-400 max-w-md mx-auto text-sm">
            ⏳ {t('wizard.step3.analyzing_warning')}
          </p>
        </div>
        <Button variant="ghost" onClick={goToPrevStep}>
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
          <h1 className="text-2xl font-bold text-app-text">{t('wizard.steps.analysis')}</h1>
          <p className="text-app-text-muted mt-1">{t('wizard.step3.description')}</p>
        </div>
        <div className="p-4 bg-app-danger-soft border border-app-danger/30 rounded-lg text-app-danger">
          {analyzeMutation.error instanceof Error
            ? analyzeMutation.error.message
            : t('common.error')}
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={goToPrevStep}>
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
        <h1 className="text-2xl font-bold text-app-text">{t('wizard.steps.analysis')}</h1>
        <p className="text-app-text-muted mt-1">{t('wizard.step3.description')}</p>
      </div>

      {hasAnalysis && (
        <div className="space-y-6">
          {/* Score */}
          <div className="bg-app-surface border border-app-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{t('wizard.step3.score')}</h2>
              <div className="flex items-center gap-3">
                {state.previousScore !== null && state.previousScore !== analysis.score && (
                  <div className="text-2xl text-app-text-subtle line-through">
                    {state.previousScore}
                  </div>
                )}
                <div
                  className={`text-4xl font-bold ${
                    analysis.score >= 70
                      ? 'text-app-success'
                      : analysis.score >= 50
                        ? 'text-app-warning'
                        : 'text-app-danger'
                  }`}
                >
                  {analysis.score}
                  <span className="text-lg text-app-text-subtle">/100</span>
                </div>
                {state.previousScore !== null && analysis.score > state.previousScore && (
                  <span className="text-sm font-medium text-app-success bg-app-success-soft px-2 py-1 rounded">
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
            <div className="bg-app-surface border border-app-border rounded-lg p-4">
              <h3 className="font-medium text-app-text mb-3">
                {t('wizard.step3.required_skills')}
              </h3>
              <div className="space-y-2">
                {analysis.matched_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis.missing_required_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis.matched_required_skills.length === 0 &&
                  analysis.missing_required_skills.length === 0 && (
                    <p className="text-sm text-app-text-subtle">{t('wizard.step3.no_data')}</p>
                  )}
              </div>
            </div>

            {/* Preferred skills */}
            <div className="bg-app-surface border border-app-border rounded-lg p-4">
              <h3 className="font-medium text-app-text mb-3">
                {t('wizard.step3.preferred_skills')}
              </h3>
              <div className="space-y-2">
                {analysis.matched_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched />
                ))}
                {analysis.missing_preferred_skills.map((skill: string) => (
                  <SkillBadge key={skill} skill={skill} matched={false} />
                ))}
                {analysis.matched_preferred_skills.length === 0 &&
                  analysis.missing_preferred_skills.length === 0 && (
                    <p className="text-sm text-app-text-subtle">{t('wizard.step3.no_data')}</p>
                  )}
              </div>
            </div>
          </div>

          {/* Gaps */}
          {analysis.gaps.length > 0 && (
            <div className="bg-app-surface border border-app-border rounded-lg p-4">
              <h3 className="font-medium text-app-text mb-3">
                {t('wizard.step3.gaps')} ({analysis.gaps.length})
              </h3>
              <div className="space-y-3">
                {analysis.gaps.map((gap: Gap) => (
                  <div
                    key={gap.id}
                    className={`p-3 rounded-lg border ${getSeverityCardClass(gap.severity)}`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle
                        className={`w-4 h-4 mt-0.5 ${getSeverityIconClass(gap.severity)}`}
                      />
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-medium text-app-text">{gap.message}</p>
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded font-semibold ${getSeverityBadgeClass(
                              gap.severity
                            )}`}
                          >
                            {gap.severity === 'high'
                              ? 'важно'
                              : gap.severity === 'medium'
                                ? 'средне'
                                : 'низкий'}
                          </span>
                        </div>
                        {gap.suggestion && (
                          <p className="text-sm text-app-text-muted mt-1">{gap.suggestion}</p>
                        )}
                        <span className="inline-block mt-1 text-xs text-app-text-subtle">
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
            <Button variant="ghost" onClick={goToPrevStep}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('common.back_to_step')} 2
            </Button>
            <Button onClick={goToNextStep} className="min-w-[150px]">
              {t('wizard.step3.improve_button')}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
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
    <div className="bg-app-surface-muted rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-app-text-muted">{label}</span>
        <span className="text-sm font-medium text-app-text">
          {value}/{maxValue}
        </span>
      </div>
      <div className="w-full bg-app-border rounded-full h-2">
        <div
          className={`h-2 rounded-full ${
            percentage >= 70
              ? 'bg-app-success'
              : percentage >= 50
                ? 'bg-app-warning'
                : 'bg-app-danger'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {comment && (
        <p className="text-xs text-app-text-subtle mt-1 truncate" title={comment}>
          {comment}
        </p>
      )}
    </div>
  )
}

function SkillBadge({ skill, matched }: { skill: string; matched: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
        matched ? 'bg-app-success-soft text-app-success' : 'bg-app-danger-soft text-app-danger'
      }`}
    >
      {matched ? (
        <CheckCircle className="w-4 h-4 text-app-success" />
      ) : (
        <XCircle className="w-4 h-4 text-app-danger" />
      )}
      {skill}
    </div>
  )
}
