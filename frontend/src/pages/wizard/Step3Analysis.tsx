import { useMutation } from '@tanstack/react-query'
import { BarChart2, Loader2, ArrowRight, ArrowLeft, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWizard } from '@/hooks'
import { analyzeMatch } from '@/api'
import type { Gap, MatchAnalysis } from '@/api'
import { Button } from '@/components'

export default function Step3Analysis() {
  const { t } = useTranslation()
  const { state, setAnalysis, goToNextStep, goToPrevStep } = useWizard()

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: () =>
      analyzeMatch({
        resume_text: state.resumeText,
        vacancy_text: state.vacancyText,
      }),
    onSuccess: (data) => {
      setAnalysis(data.analysis_id, data.analysis)
    },
  })

  const handleAnalyze = () => {
    analyzeMutation.mutate()
  }

  const analysis = state.analysis
  const hasAnalysis = !!analysis

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('wizard.steps.analysis')}</h1>
        <p className="text-gray-500 mt-1">
          {hasAnalysis
            ? t('wizard.step3.description')
            : t('wizard.step3.description')}
        </p>
      </div>

      {!hasAnalysis ? (
        <div className="space-y-4">
          {/* Preview cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">{t('wizard.steps.resume')}</h3>
              <p className="text-sm text-gray-600">
                {state.parsedResume?.personal_info?.name || 'Кандидат'}
                {state.parsedResume?.personal_info?.title && (
                  <span className="text-gray-400">
                    {' '}
                    — {state.parsedResume.personal_info.title}
                  </span>
                )}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {state.parsedResume?.skills?.length || 0} навыков,{' '}
                {state.parsedResume?.work_experience?.length || 0} мест работы
              </p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">{t('wizard.steps.vacancy')}</h3>
              <p className="text-sm text-gray-600">
                {state.parsedVacancy?.job_title || 'Вакансия'}
                {state.parsedVacancy?.company && (
                  <span className="text-gray-400"> — {state.parsedVacancy.company}</span>
                )}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {state.parsedVacancy?.required_skills?.length || 0} обязательных навыков
              </p>
            </div>
          </div>

          {/* Analyze button */}
          <div className="flex justify-center py-8">
            <Button
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending}
              className="min-w-[200px]"
              size="lg"
            >
              {analyzeMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  {t('wizard.step1.analyzing')}
                </>
              ) : (
                <>
                  <BarChart2 className="w-5 h-5 mr-2" />
                  {t('wizard.step2.analyze_button')}
                </>
              )}
            </Button>
          </div>

          {analyzeMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {analyzeMutation.error instanceof Error
                ? analyzeMutation.error.message
                : t('common.error')}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-start pt-4">
            <Button variant="outline" onClick={goToPrevStep}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('wizard.step2.back')}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Score */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{t('wizard.step3.score')}</h2>
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
            <Button variant="outline" onClick={goToPrevStep}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t('wizard.step2.back')}
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
