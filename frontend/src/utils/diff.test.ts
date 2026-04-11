import { computeDiff, escapeHtml } from './diff'

describe('computeDiff', () => {
  it('returns no changes for identical strings', () => {
    const result = computeDiff('hello world', 'hello world')
    expect(result.stats.added).toBe(0)
    expect(result.stats.removed).toBe(0)
    expect(result.segments.every((s) => s.type === 'equal')).toBe(true)
  })

  it('detects added words', () => {
    const result = computeDiff('hello', 'hello world')
    expect(result.stats.added).toBeGreaterThan(0)
    expect(result.segments.some((s) => s.type === 'add')).toBe(true)
  })

  it('detects removed words', () => {
    const result = computeDiff('hello world', 'hello')
    expect(result.stats.removed).toBeGreaterThan(0)
    expect(result.segments.some((s) => s.type === 'remove')).toBe(true)
  })

  it('handles empty strings', () => {
    const result = computeDiff('', '')
    expect(result.stats.added).toBe(0)
    expect(result.stats.removed).toBe(0)
  })

  it('handles full replacement', () => {
    const result = computeDiff('abc', 'xyz')
    expect(result.stats.removed).toBeGreaterThan(0)
    expect(result.stats.added).toBeGreaterThan(0)
  })

  it('supports line granularity', () => {
    const before = 'line1\nline2\nline3'
    const after = 'line1\nmodified\nline3'
    const result = computeDiff(before, after, 'line')
    expect(result.segments.some((s) => s.type === 'add')).toBe(true)
    expect(result.segments.some((s) => s.type === 'remove')).toBe(true)
  })

  it('supports word granularity by default', () => {
    const result = computeDiff('the quick brown fox', 'the slow brown fox')
    const added = result.segments.filter((s) => s.type === 'add')
    const removed = result.segments.filter((s) => s.type === 'remove')
    expect(added.length).toBeGreaterThan(0)
    expect(removed.length).toBeGreaterThan(0)
  })
})

describe('escapeHtml', () => {
  it('escapes angle brackets', () => {
    expect(escapeHtml('<script>')).toBe('&lt;script&gt;')
  })

  it('escapes ampersands', () => {
    expect(escapeHtml('a & b')).toBe('a &amp; b')
  })

  it('escapes quotes', () => {
    expect(escapeHtml('"hello"')).toBe('&quot;hello&quot;')
  })

  it('escapes single quotes', () => {
    expect(escapeHtml("it's")).toBe("it&#039;s")
  })

  it('leaves plain text unchanged', () => {
    expect(escapeHtml('hello world')).toBe('hello world')
  })
})
