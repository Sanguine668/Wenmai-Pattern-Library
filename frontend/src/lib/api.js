const configuredBase = import.meta.env.VITE_API_BASE || ''
export const API_BASE = configuredBase.replace(/\/$/, '')

const TOKEN_KEY = 'wenmai:token'

export function authToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setAuthToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Local storage may be unavailable in private mode.
  }
}

export function clearAuthToken() {
  setAuthToken('')
}

export async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = authToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (response.status === 401 && token) {
    const isAuthAttempt =
      path === '/api/auth/login' || path === '/api/auth/register'
    if (!isAuthAttempt) {
      window.dispatchEvent(new CustomEvent('wenmai:unauthorized'))
    }
  }
  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch {
      // Keep the status message when the response has no JSON body.
    }
    throw new Error(message)
  }
  if (response.status === 204) return null
  return response.json()
}

export function apiAsset(path) {
  if (!path || /^https?:\/\//i.test(path)) return path
  return path.startsWith('/api/') ? `${API_BASE}${path}` : path
}
