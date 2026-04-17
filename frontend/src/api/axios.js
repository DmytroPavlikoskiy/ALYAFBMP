import axios from 'axios'

/** Без завершального /api/v1 — додаємо нижче. */
const HTTP_ORIGIN =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000'
const API_ROOT = `${HTTP_ORIGIN}/api/v1`

const api = axios.create({
  baseURL: API_ROOT,
  headers: { 'Content-Type': 'application/json' },
})

/** Один спільний refresh на всі паралельні 401 — інакше другий refresh зі старим refresh_token дає 401. */
let refreshInFlight = null

function refreshAccessToken() {
  if (!refreshInFlight) {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) {
      return Promise.reject(new Error('No refresh token'))
    }
    refreshInFlight = axios
      .post(`${API_ROOT}/auth/refresh`, { refresh_token: refresh })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        window.dispatchEvent(new CustomEvent('auth:access-token-changed'))
        return data
      })
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

function isRefreshRequest(config) {
  const path = config?.url || ''
  return path.includes('auth/refresh')
}

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401 (single-flight)
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }
    if (!original || isRefreshRequest(original)) {
      return Promise.reject(error)
    }
    if (original._retry) {
      return Promise.reject(error)
    }
    original._retry = true

    try {
      const data = await refreshAccessToken()
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(error)
    }
  }
)

export default api
