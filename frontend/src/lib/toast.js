import { ref } from 'vue'

export const toasts = ref([])
let nextId = 0

export function dismissToast(id) {
  toasts.value = toasts.value.filter((item) => item.id !== id)
}

export function notify(message, tone = 'info') {
  const id = ++nextId
  toasts.value.push({ id, message, tone })
  window.setTimeout(() => dismissToast(id), 2800)
}
