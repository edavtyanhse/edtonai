const CLARITY_PROJECT_ID = import.meta.env.VITE_CLARITY_PROJECT_ID

let initialized = false

type ClarityFn = ((...args: unknown[]) => void) & {
  q?: unknown[][]
}

export function initClarity(): void {
  if (
    !CLARITY_PROJECT_ID ||
    initialized ||
    typeof window === 'undefined' ||
    typeof document === 'undefined'
  ) {
    return
  }

  const w = window as Window & {
    clarity?: ClarityFn
  }

  if (!w.clarity) {
    const clarity = ((...args: unknown[]) => {
      clarity.q = clarity.q ?? []
      clarity.q.push(args)
    }) as ClarityFn

    w.clarity = clarity
  }

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.clarity.ms/tag/${CLARITY_PROJECT_ID}`
  script.dataset.clarityProjectId = CLARITY_PROJECT_ID

  const firstScript = document.getElementsByTagName('script')[0]
  if (firstScript?.parentNode) {
    firstScript.parentNode.insertBefore(script, firstScript)
  } else {
    document.head.appendChild(script)
  }

  initialized = true
}
