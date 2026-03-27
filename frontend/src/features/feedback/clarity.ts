const CLARITY_PROJECT_ID = import.meta.env.VITE_CLARITY_PROJECT_ID

let initialized = false

export function initClarity(): void {
  if (!CLARITY_PROJECT_ID || initialized || typeof window === 'undefined') {
    return
  }

  const w = window as Window & {
    clarity?: (...args: unknown[]) => void
  }

  w.clarity = w.clarity ?? (() => undefined)

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.clarity.ms/tag/${CLARITY_PROJECT_ID}`
  document.head.appendChild(script)

  initialized = true
}
