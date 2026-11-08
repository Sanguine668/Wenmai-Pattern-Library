import { computed, ref } from 'vue'
import { apiFetch, authToken, clearAuthToken, setAuthToken } from './api'

const currentUser = ref(null)
const ready = ref(false)
const pending = ref(false)
let sessionPromise = null

export const isAuthenticated = computed(() => Boolean(currentUser.value))
export const isAdmin = computed(() => Boolean(currentUser.value?.isAdmin))

function announce() {
  window.dispatchEvent(new CustomEvent('wenmai:auth-changed'))
}

function applySession(payload) {
  setAuthToken(payload.token)
  currentUser.value = payload.user
  ready.value = true
  announce()
  return payload.user
}

export function clearSession() {
  clearAuthToken()
  currentUser.value = null
  ready.value = true
  announce()
}

export async function restoreSession() {
  if (!authToken()) {
    currentUser.value = null
    ready.value = true
    return null
  }
  try {
    currentUser.value = await apiFetch('/api/auth/me')
  } catch {
    clearSession()
  } finally {
    ready.value = true
  }
  return currentUser.value
}

export function ensureSession() {
  if (!sessionPromise) {
    sessionPromise = restoreSession().finally(() => {
      // 网络失败后允许下次导航重试；已登录时保持缓存。
      if (!currentUser.value) sessionPromise = null
    })
  }
  return sessionPromise
}

export async function login(username, password) {
  pending.value = true
  try {
    const payload = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    return applySession(payload)
  } finally {
    pending.value = false
  }
}

export async function register({ username, displayName, password, email }) {
  pending.value = true
  try {
    const payload = await apiFetch('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username,
        display_name: displayName,
        password,
        email: email || null,
      }),
    })
    return applySession(payload)
  } finally {
    pending.value = false
  }
}

export function logout() {
  clearSession()
}

window.addEventListener('wenmai:unauthorized', clearSession)

export function useAuth() {
  return {
    currentUser,
    ready,
    pending,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    restoreSession,
    ensureSession,
  }
}
