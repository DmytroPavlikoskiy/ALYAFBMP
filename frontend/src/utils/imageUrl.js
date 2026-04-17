/**
 * Product images from the API may be:
 * - a list of URL strings: ["static/products/a.jpg", ...]
 * - or legacy objects: [{ image_url: "..." }]
 *
 * Static files are served by FastAPI at /static/... — prepend the API origin
 * (Vite runs on another port, so relative paths would 404).
 */
const BACKEND =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000'

export function resolveProductImageUrl(entry) {
  if (entry == null) return null
  const raw = typeof entry === 'string' ? entry : entry.image_url
  if (!raw) return null
  if (/^https?:\/\//.test(raw)) return raw
  return `${BACKEND}/${String(raw).replace(/^\//, '')}`
}
