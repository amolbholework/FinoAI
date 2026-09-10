import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// withCredentials so the httpOnly session cookies (set by the backend on
// /api/auth/*) are sent with every request.
export const api = axios.create({ baseURL: API_BASE_URL, withCredentials: true })

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

// Access tokens are short-lived (15 min) by design. Rather than make every
// page handle "my session just expired mid-use", a 401 triggers one silent
// refresh attempt and replays the original request — concurrent 401s queue
// behind a single refresh call instead of each firing their own.
let refreshPromise: Promise<boolean> | null = null

async function refreshSession(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = api
      .post('/api/auth/refresh')
      .then(() => true)
      .catch(() => false)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined
    const isAuthEndpoint = config?.url?.startsWith('/api/auth/')

    if (error.response?.status === 401 && config && !config._retried && !isAuthEndpoint) {
      config._retried = true
      const refreshed = await refreshSession()
      if (refreshed) return api(config)
    }

    return Promise.reject(error)
  },
)
