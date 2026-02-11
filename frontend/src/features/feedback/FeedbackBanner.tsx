/**
 * FEEDBACK FEATURE - Banner Component for Home Page
 * TO REMOVE: Delete this file
 */

import { MessageSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FEEDBACK_CONFIG } from './config'
import Button from '@/components/Button'

interface FeedbackBannerProps {
  onClick: () => void
}

export function FeedbackBanner({ onClick }: FeedbackBannerProps) {
  const { i18n } = useTranslation()
  
  if (!FEEDBACK_CONFIG.enabled) return null

  const lang = i18n.language as 'ru' | 'en'
  const message = FEEDBACK_CONFIG.bannerMessage[lang]

  return (
    <div className="bg-gradient-to-r from-brand-600/20 to-purple-600/20 border border-brand-500/30 rounded-lg p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-5 h-5 text-brand-400 flex-shrink-0" />
          <p className="text-sm text-slate-300">{message}</p>
        </div>
        <Button
          size="sm"
          variant="primary"
          onClick={onClick}
          icon={<MessageSquare />}
        >
          {lang === 'ru' ? 'Оставить отзыв' : 'Leave feedback'}
        </Button>
      </div>
    </div>
  )
}
