/**
 * WebSocket URL for chat — must match FastAPI mount: /api/v1 (see main.py + communication router).
 * Uses the same origin as REST (VITE_API_BASE_URL), so Docker / HTTPS / LAN keep working.
 */
const HTTP_ORIGIN =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000'

/**
 * @param {string} chatId - UUID
 * @param {string} token - JWT access token
 */
export function getChatWebSocketUrl(chatId, token) {
  const wsOrigin = HTTP_ORIGIN.replace(/^http/, 'ws')
  const q = new URLSearchParams({ token })
  return `${wsOrigin}/api/v1/ws/chat/${chatId}?${q.toString()}`
}
