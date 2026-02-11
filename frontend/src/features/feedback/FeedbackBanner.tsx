/**
 * FEEDBACK FEATURE - Banner Component
 * TO REMOVE: Delete this file
 */

import { MessageSquare, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FEEDBACK_CONFIG } from './config'

interface FeedbackBannerProps {
  onClick: () => void
}

export function FeedbackBanner({ onClick }: FeedbackBannerProps) {
  const { i18n } = useTranslation()
  
  if (!FEEDBACK_CONFIG.enabled) return null

  const lang = (i18n.language?.split('-')[0] || 'ru') as 'ru' | 'en'

  const title = lang === 'ru'
    ? 'Помогите нам стать лучше!'
    : 'Help us improve!'

  const description = lang === 'ru'
    ? 'Мы активно развиваем продукт и сейчас собираем обратную связь. Расскажите, что вам понравилось, что можно улучшить или какие функции вы хотели бы видеть — это займёт меньше минуты.'
    : 'We are actively developing the product and collecting feedback. Tell us what you liked, what could be improved, or what features you would like to see — it takes less than a minute.'

  const buttonText = lang === 'ru' ? 'Оставить отзыв' : 'Leave feedback'

  return (
    <div
      className="bg-gradient-to-r from-brand-600/10 via-purple-600/10 to-brand-600/10 border border-brand-500/30 rounded-xl p-6 cursor-pointer hover:border-brand-400/50 transition-all group"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-shrink-0 w-12 h-12 bg-brand-500/20 rounded-xl flex items-center justify-center">
          <MessageSquare className="w-6 h-6 text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <Sparkles className="w-4 h-4 text-yellow-400" />
          </div>
          <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
        </div>
        <div className="flex-shrink-0 self-center">
          <span className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-lg transition-colors group-hover:bg-brand-500">
            <MessageSquare className="w-4 h-4" />
            {buttonText}
          </span>
        </div>
      </div>
    </div>
  )
}
