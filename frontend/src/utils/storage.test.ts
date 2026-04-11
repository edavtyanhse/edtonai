import { saveDraft, loadDraft, clearDraft, debounce } from './storage'

describe('storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('saveDraft / loadDraft', () => {
    it('saves and loads a draft', () => {
      saveDraft({ resumeText: 'resume', vacancyText: 'vacancy', resultText: 'result' })
      const draft = loadDraft()
      expect(draft).not.toBeNull()
      expect(draft!.resumeText).toBe('resume')
      expect(draft!.vacancyText).toBe('vacancy')
      expect(draft!.resultText).toBe('result')
    })

    it('includes timestamps', () => {
      saveDraft({ resumeText: '', vacancyText: '', resultText: '' })
      const draft = loadDraft()
      expect(draft!.savedAt).toBeGreaterThan(0)
      expect(draft!.expiresAt).toBeGreaterThan(draft!.savedAt)
    })

    it('returns null when no draft exists', () => {
      expect(loadDraft()).toBeNull()
    })

    it('returns null for expired drafts', () => {
      saveDraft({ resumeText: 'test', vacancyText: '', resultText: '' })
      // Manually expire
      const stored = JSON.parse(localStorage.getItem('edtonai_draft')!)
      stored.expiresAt = Date.now() - 1000
      localStorage.setItem('edtonai_draft', JSON.stringify(stored))
      expect(loadDraft()).toBeNull()
    })

    it('returns null for invalid JSON', () => {
      localStorage.setItem('edtonai_draft', 'not-json')
      expect(loadDraft()).toBeNull()
    })

    it('returns null for invalid structure', () => {
      localStorage.setItem('edtonai_draft', JSON.stringify({ foo: 'bar' }))
      expect(loadDraft()).toBeNull()
    })
  })

  describe('clearDraft', () => {
    it('removes the draft from storage', () => {
      saveDraft({ resumeText: 'test', vacancyText: '', resultText: '' })
      clearDraft()
      expect(loadDraft()).toBeNull()
    })

    it('does not throw when no draft exists', () => {
      expect(() => clearDraft()).not.toThrow()
    })
  })

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })
    afterEach(() => {
      vi.useRealTimers()
    })

    it('delays function execution', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)

      debounced()
      expect(fn).not.toHaveBeenCalled()

      vi.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('resets delay on subsequent calls', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)

      debounced()
      vi.advanceTimersByTime(50)
      debounced()
      vi.advanceTimersByTime(50)
      expect(fn).not.toHaveBeenCalled()

      vi.advanceTimersByTime(50)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('passes arguments to the original function', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)

      debounced('arg1', 'arg2')
      vi.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledWith('arg1', 'arg2')
    })
  })
})
