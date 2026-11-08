import { computed, ref } from 'vue'
import { apiAsset, apiFetch } from './api'

const FAVORITES_KEY = 'wenmai:favorites'
const HISTORY_KEY = 'wenmai:history'

function readIds(key) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeIds(key, ids) {
  try {
    localStorage.setItem(key, JSON.stringify(ids))
  } catch {
    // Local storage may be unavailable in private mode.
  }
}

const favoriteIds = ref(readIds(FAVORITES_KEY))
const historyIds = ref(readIds(HISTORY_KEY))
const favoriteItems = ref([])
const historyItems = ref([])
const syncing = ref(false)
const favoritesCount = computed(() => favoriteIds.value.length)

async function hydrateUserLibrary() {
  syncing.value = true
  try {
    const [favorites, history] = await Promise.all([
      apiFetch('/api/me/favorites'),
      apiFetch('/api/me/history?limit=30'),
    ])
    favoriteItems.value = favorites.items.map((item) => ({
      ...item,
      image: apiAsset(item.image),
    }))
    historyItems.value = history.items.map((item) => ({
      ...item,
      image: apiAsset(item.image),
    }))
    favoriteIds.value = favorites.items.map((item) => item.id)
    historyIds.value = history.items.map((item) => item.id)
    writeIds(FAVORITES_KEY, favoriteIds.value)
    writeIds(HISTORY_KEY, historyIds.value)
  } catch {
    // Keep the browser copy available when the backend is offline.
  } finally {
    syncing.value = false
  }
}

function isFavorite(id) {
  return favoriteIds.value.includes(id)
}

async function toggleFavorite(id) {
  if (!id) return
  const wasFavorite = isFavorite(id)
  if (wasFavorite) {
    favoriteIds.value = favoriteIds.value.filter((item) => item !== id)
    favoriteItems.value = favoriteItems.value.filter((item) => item.id !== id)
  } else {
    favoriteIds.value = [id, ...favoriteIds.value]
  }
  writeIds(FAVORITES_KEY, favoriteIds.value)
  try {
    await apiFetch(`/api/me/favorites/${id}`, {
      method: wasFavorite ? 'DELETE' : 'POST',
    })
    await hydrateUserLibrary()
  } catch {
    // The local state remains usable without the API.
  }
}

function recordView(id) {
  if (!id) return
  historyIds.value = [id, ...historyIds.value.filter((item) => item !== id)].slice(0, 30)
  writeIds(HISTORY_KEY, historyIds.value)
  apiFetch(`/api/me/views/${id}`, { method: 'POST' })
    .then(hydrateUserLibrary)
    .catch(() => {})
}

function resetLocalLibrary() {
  favoriteIds.value = []
  historyIds.value = []
  favoriteItems.value = []
  historyItems.value = []
  writeIds(FAVORITES_KEY, [])
  writeIds(HISTORY_KEY, [])
}

export function useLibrary() {
  return {
    favoriteIds,
    historyIds,
    favoriteItems,
    historyItems,
    syncing,
    favoritesCount,
    hydrateUserLibrary,
    isFavorite,
    toggleFavorite,
    recordView,
  }
}

// 登录 / 退出 / 会话失效后先清空上一账号的本地数据，再同步当前身份（游客为 demo）。
window.addEventListener('wenmai:auth-changed', () => {
  resetLocalLibrary()
  hydrateUserLibrary()
})
