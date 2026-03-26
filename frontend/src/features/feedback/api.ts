/**
 * FEEDBACK FEATURE - API Integration
 * TO REMOVE: Delete this file
 */

import { apiClient } from '@/api/client'

export interface FeedbackSubmit {
  metric_type: 'csat' | 'nps'
  score: number
  feedback_text: string
  context_step?: string
  ui_variant?: string
  user_segment?: string
}

export interface FeedbackResponse {
  id: number
  user_email: string
  metric_type: 'csat' | 'nps'
  score: number
  feedback_text: string
  context_step: string | null
  ui_variant: string | null
  user_segment: string | null
  created_at: string
}

export async function submitFeedback(data: FeedbackSubmit): Promise<FeedbackResponse> {
  return apiClient.post<FeedbackResponse>('/v1/feedback', data)
}
