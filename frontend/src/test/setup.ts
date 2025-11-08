import "@testing-library/jest-dom/vitest";

// jsdom does not implement crypto.randomUUID by default in older versions.
if (!globalThis.crypto?.randomUUID) {
  globalThis.crypto = {
    ...globalThis.crypto,
    randomUUID: () => `test-${Math.random().toString(36).slice(2, 10)}`,
  } as Crypto;
}
