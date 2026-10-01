// Client for the Python lexer server (backend/server.py), reached through the Vite /api proxy.

export const SERVER_HINT = 'Start the Python lexer server in another terminal: npm run lexer';

async function request(path, options) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error(`Cannot reach the Python lexer server. ${SERVER_HINT}`);
  }
  // The Vite proxy answers 5xx when the Python server is not running.
  if (response.status >= 500) {
    throw new Error(`Cannot reach the Python lexer server. ${SERVER_HINT}`);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Lexer server error (HTTP ${response.status}).`);
  }
  return body;
}

export function lexSource(source) {
  return request('/api/lex', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source }),
  });
}

export function fetchKeywords() {
  return request('/api/keywords');
}
