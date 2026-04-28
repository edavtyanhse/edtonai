import '@testing-library/jest-dom'

import { beforeEach } from 'vitest'

class InMemoryStorage implements Storage {
  private readonly items = new Map<string, string>()

  get length(): number {
    return this.items.size
  }

  clear(): void {
    this.items.clear()
  }

  getItem(key: string): string | null {
    return this.items.get(key) ?? null
  }

  key(index: number): string | null {
    return Array.from(this.items.keys())[index] ?? null
  }

  removeItem(key: string): void {
    this.items.delete(key)
  }

  setItem(key: string, value: string): void {
    this.items.set(key, value)
  }
}

const testStorage = new InMemoryStorage()

Object.defineProperty(globalThis, 'localStorage', {
  value: testStorage,
  configurable: true,
})

Object.defineProperty(window, 'localStorage', {
  value: testStorage,
  configurable: true,
})

beforeEach(() => {
  testStorage.clear()
})
