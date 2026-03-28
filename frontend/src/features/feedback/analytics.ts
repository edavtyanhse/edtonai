import { apiClient } from '@/api/client'

const SESSION_ID_KEY = 'edtonai_analytics_session_id'
const UI_VARIANT_KEY = 'edtonai_ui_variant'

export interface AnalyticsEventPayload {
  event_name: string
  session_id: string
  step?: string
  ui_variant?: string
  user_segment?: string
  occurred_at?: string
  properties?: Record<string, unknown>
}

function randomId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}

export function getSessionId(): string {
  const existing = localStorage.getItem(SESSION_ID_KEY)
  if (existing) return existing

  const created = randomId('sess')
  localStorage.setItem(SESSION_ID_KEY, created)
  return created
}

export function getUiVariant(): 'A' | 'B' {
  const existing = localStorage.getItem(UI_VARIANT_KEY)
  if (existing === 'A' || existing === 'B') return existing

  const variant: 'A' | 'B' = Math.random() < 0.5 ? 'A' : 'B'
  localStorage.setItem(UI_VARIANT_KEY, variant)
  return variant
}

export async function sendAnalyticsEvent(payload: AnalyticsEventPayload): Promise<void> {
  await apiClient.post('/v1/analytics/events', payload)
}

export function trackBehaviorEvent(
  eventName: string,
  data?: {
    step?: string
    userSegment?: string
    properties?: Record<string, unknown>
  }
): void {
  const payload: AnalyticsEventPayload = {
    event_name: eventName,
    session_id: getSessionId(),
    step: data?.step,
    ui_variant: getUiVariant(),
    user_segment: data?.userSegment ?? 'job_seeker',
    occurred_at: new Date().toISOString(),
    properties: data?.properties ?? {},
  }

  void sendAnalyticsEvent(payload).catch((error) => {
    console.warn('Failed to send analytics event:', error)
  })
}
