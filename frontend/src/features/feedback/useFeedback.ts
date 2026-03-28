/**
 * FEEDBACK FEATURE - Hook for managing feedback state
 * TO REMOVE: Delete this file
 */

import { useState } from 'react'
import { FEEDBACK_CONFIG } from './config'

const FEEDBACK_SHOWN_KEY = 'feedback_modal_shown'
type FeedbackSource = 'auto' | 'manual' | 'result'

export function useFeedback() {
  const [isOpen, setIsOpen] = useState(false)
  const [source, setSource] = useState<FeedbackSource>('manual')
  const [hasShownAuto, setHasShownAuto] = useState(() => {
    if (typeof window === 'undefined') return true
    return localStorage.getItem(FEEDBACK_SHOWN_KEY) === 'true'
  })

  const showFeedback = (nextSource: FeedbackSource = 'manual') => {
    if (!FEEDBACK_CONFIG.enabled) return
    setSource(nextSource)
    setIsOpen(true)
  }

  const showFeedbackAuto = (): boolean => {
    if (!FEEDBACK_CONFIG.enabled || !FEEDBACK_CONFIG.showAfterAnalysis) return false
    if (hasShownAuto) return false

    setSource('auto')
    setIsOpen(true)
    setHasShownAuto(true)
    localStorage.setItem(FEEDBACK_SHOWN_KEY, 'true')
    return true
  }

  const closeFeedback = () => {
    setIsOpen(false)
  }

  return {
    isOpen,
    showFeedback,
    showFeedbackAuto,
    closeFeedback,
    source,
    isEnabled: FEEDBACK_CONFIG.enabled,
  }
}
