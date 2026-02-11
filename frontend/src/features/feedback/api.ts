/**
 * FEEDBACK FEATURE - API Integration
 * TO REMOVE: Delete this file
 */

import { api } from '@/api/client'

export interface FeedbackSubmit {
  feedback_text: string
}

export interface FeedbackResponse {
  id: number
  user_email: string
  feedback_text: string
  created_at: string
}

export async function submitFeedback(data: FeedbackSubmit): Promise<FeedbackResponse> {
  const response = await api.post<FeedbackResponse>('/v1/feedback', data)
  return response.data
}
