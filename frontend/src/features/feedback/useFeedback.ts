/**
 * FEEDBACK FEATURE - Hook for managing feedback state
 * TO REMOVE: Delete this file
 */

import { useState, useEffect } from 'react'
import { FEEDBACK_CONFIG } from './config'

const FEEDBACK_SHOWN_KEY = 'feedback_modal_shown'

export function useFeedback() {
  const [isOpen, setIsOpen] = useState(false)
  const [hasShownAuto, setHasShownAuto] = useState(() => {
    if (typeof window === 'undefined') return true
    return localStorage.getItem(FEEDBACK_SHOWN_KEY) === 'true'
  })

  const showFeedback = () => {
    if (!FEEDBACK_CONFIG.enabled) return
    setIsOpen(true)
  }

  const showFeedbackAuto = (): boolean => {
    if (!FEEDBACK_CONFIG.enabled || !FEEDBACK_CONFIG.showAfterAnalysis) return false
    if (hasShownAuto) return false
    
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
    isEnabled: FEEDBACK_CONFIG.enabled,
  }
}
