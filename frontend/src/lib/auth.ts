const USER_STORAGE_KEY = "edton.user";
const isBrowser = typeof window !== "undefined" && typeof window.localStorage !== "undefined";
let cachedUserId: string | null = null;

function generateUserId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `user-${Math.random().toString(36).slice(2, 10)}`;
}

export function getUserId(): string {
  if (cachedUserId) {
    return cachedUserId;
  }
  if (!isBrowser) {
    cachedUserId = "test-user";
    return cachedUserId;
  }
  const stored = window.localStorage.getItem(USER_STORAGE_KEY);
  if (stored) {
    cachedUserId = stored;
    return stored;
  }
  const userId = generateUserId();
  window.localStorage.setItem(USER_STORAGE_KEY, userId);
  cachedUserId = userId;
  return userId;
}
