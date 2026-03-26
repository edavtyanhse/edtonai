/**
 * FEEDBACK FEATURE - Modal Component
 * TO REMOVE: Delete this file
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, Send, Loader2, CheckCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { submitFeedback } from './api'
import { getUiVariant, trackBehaviorEvent } from './analytics'
import { FEEDBACK_CONFIG } from './config'
import Button from '@/components/Button'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  source?: 'auto' | 'manual' | 'result'
}

export function FeedbackModal({ isOpen, onClose, source: _source = 'manual' }: FeedbackModalProps) {
  const { i18n } = useTranslation()
  const [feedback, setFeedback] = useState('')
  const [score, setScore] = useState<number | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const metricType = _source === 'result' ? 'csat' : 'nps'

  const handleClose = () => {
    setFeedback('')
    setScore(null)
    setSubmitted(false)
    onClose()
  }

  const mutation = useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => {
      setSubmitted(true)
    },
  })

  const handleSubmit = () => {
    if (feedback.trim().length === 0 || score === null) return
    mutation.mutate({
      metric_type: metricType,
      score,
      feedback_text: feedback,
      context_step: _source === 'result' ? 'wizard_result' : 'wizard_done',
      ui_variant: getUiVariant(),
      user_segment: 'job_seeker',
    })
    trackBehaviorEvent('feedback_submitted', {
      step: _source === 'result' ? 'step_4_result' : 'step_4_done',
      properties: {
        metric_type: metricType,
        score,
        source: _source,
      },
    })
  }

  if (!isOpen) return null

  const lang = (i18n.language?.split('-')[0] || 'ru') as 'ru' | 'en'
  const title = lang === 'ru' ? 'Оставьте отзыв' : 'Leave feedback'
  const placeholder = FEEDBACK_CONFIG.placeholder[lang] || FEEDBACK_CONFIG.placeholder['ru']

  const scoreTitle = metricType === 'csat'
    ? (lang === 'ru' ? 'Оцените качество результата (1–5)' : 'Rate result quality (1-5)')
    : (lang === 'ru' ? 'Насколько вероятно, что вы порекомендуете сервис? (0–10)' : 'How likely are you to recommend us? (0-10)')

  const description = lang === 'en'
    ? 'We are actively developing the product and your opinion is very important to us. Tell us what you liked, what could be improved, or what features you would like to see.'
    : 'Мы активно развиваем продукт и ваше мнение очень важно для нас. Расскажите, что понравилось, что можно улучшить или какие функции хотелось бы видеть.'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 rounded-lg shadow-xl flex flex-col mx-4 border border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-2xl font-bold text-white">{title}</h2>
          <button
            onClick={handleClose}
            className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800"
            disabled={mutation.isPending}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {submitted ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
              <p className="text-xl font-semibold text-white mb-2">
                Спасибо за отзыв!
              </p>
              <p className="text-slate-400 mb-6">
                Ваше мнение помогает нам становиться лучше
              </p>
              <Button variant="primary" onClick={handleClose}>
                Закрыть
              </Button>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-400 mb-4">{description}</p>
              <div className="mb-4">
                <p className="text-sm text-slate-300 mb-2">{scoreTitle}</p>
                <div className="flex flex-wrap gap-2">
                  {(metricType === 'csat' ? [1, 2, 3, 4, 5] : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setScore(value)}
                      className={`h-9 w-9 rounded-md border text-sm font-medium transition-colors ${score === value
                        ? 'bg-brand-600 border-brand-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      disabled={mutation.isPending}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder={placeholder}
                rows={6}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
                disabled={mutation.isPending}
              />
              {mutation.isError && (
                <p className="mt-2 text-sm text-red-400">
                  {lang === 'ru' 
                    ? 'Ошибка отправки. Попробуйте позже.' 
                    : 'Error sending feedback. Please try again.'}
                </p>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!submitted && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-700">
            <Button variant="ghost" onClick={handleClose} disabled={mutation.isPending}>
              {lang === 'ru' ? 'Отмена' : 'Отмена'}
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={feedback.trim().length === 0 || score === null || mutation.isPending}
              icon={mutation.isPending ? <Loader2 className="animate-spin" /> : <Send />}
            >
              {lang === 'ru' ? 'Отправить' : 'Отправить'}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
