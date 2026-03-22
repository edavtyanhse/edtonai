/**
 * Auth API calls — register, login, refresh, logout, verify.
 * Uses credentials: 'include' for httpOnly cookie transport.
 */

const BASE_URL = '/api'

export interface UserResponse {
  id: string
  email: string
  is_email_verified: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserResponse
}

async function authFetch<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: body !== undefined ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // send httpOnly cookies
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const err = await response.json()
      detail = typeof err.detail === 'string' ? err.detail : detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }

  return response.json()
}

export function loginApi(email: string, password: string): Promise<AuthResponse> {
  return authFetch<AuthResponse>('/auth/login', { email, password })
}

export function registerApi(email: string, password: string): Promise<AuthResponse> {
  return authFetch<AuthResponse>('/auth/register', { email, password })
}

export function refreshTokenApi(): Promise<AuthResponse> {
  return authFetch<AuthResponse>('/auth/refresh', {})
}

export async function logoutApi(): Promise<void> {
  await authFetch<{ message: string }>('/auth/logout', {})
}

export function verifyEmailApi(token: string): Promise<{ message: string }> {
  return authFetch<{ message: string }>('/auth/verify-email', { token })
}
