/**
 * In-memory access token storage.
 * Access tokens are NOT stored in localStorage for security.
 */

let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function clearTokens(): void {
  accessToken = null
}
