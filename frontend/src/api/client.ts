import { supabase } from '@/lib/supabase'
import type { ApiError } from './types'

const BASE_URL = '/api'

export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`
    }
  } catch (error) {
    console.warn('Failed to get auth session:', error)
  }

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: unknown
    try {
      const errorBody: ApiError = await response.json()
      detail = errorBody.detail
    } catch {
      detail = response.statusText
    }

    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((e) => e.msg).join(', ')
          : `Request failed: ${response.status}`

    throw new ApiClientError(message, response.status, detail)
  }

  return response.json()
}

interface RequestOptions {
  signal?: AbortSignal
}

export const apiClient = {
  async get<T>(path: string, options?: RequestOptions): Promise<T> {
    const headers = await getAuthHeaders()
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'GET',
      headers,
      signal: options?.signal,
    })
    return handleResponse<T>(response)
  },

  async post<T, D = unknown>(path: string, data: D, options?: RequestOptions): Promise<T> {
    const headers = await getAuthHeaders()
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal: options?.signal,
    })
    return handleResponse<T>(response)
  },

  async delete(path: string, options?: RequestOptions): Promise<void> {
    const headers = await getAuthHeaders()
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers,
      signal: options?.signal,
    })

    if (!response.ok) {
      let detail: unknown
      try {
        const errorBody = await response.json()
        detail = errorBody.detail
      } catch {
        detail = response.statusText
      }

      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((e) => e.msg).join(', ')
            : `Request failed: ${response.status}`

      throw new ApiClientError(message, response.status, detail)
    }
    // 204 No Content - no body to parse
  },

  async patch<T, D = unknown>(path: string, data: D, options?: RequestOptions): Promise<T> {
    const headers = await getAuthHeaders()
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(data),
      signal: options?.signal,
    })
    return handleResponse<T>(response)
  },
}
