import { ref } from 'vue'
import { apiFetch } from './api'
import { libraryStats as fallbackStats } from '../data/patterns'

const stats = ref({ ...fallbackStats })
const loaded = ref(false)

export async function loadLibraryStats() {
  if (loaded.value) return stats.value
  try {
    const data = await apiFetch('/api/stats')
    stats.value = { ...fallbackStats, ...data }
    loaded.value = true
  } catch {
    // 后端离线时保留静态兜底值。
  }
  return stats.value
}

export function useLibraryStats() {
  return { stats, statsLoaded: loaded, loadLibraryStats }
}
