export function readStorage(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value === null ? fallback : value;
  } catch {
    return fallback;
  }
}

export function writeStorage(key, value) {
  try {
    localStorage.setItem(key, String(value));
  } catch {
    // Storage unavailable (private mode, blocked site data) — ignore.
  }
}
