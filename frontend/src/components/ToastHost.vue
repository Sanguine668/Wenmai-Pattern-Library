<script setup>
import { dismissToast, toasts } from '../lib/toast'
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <button
      v-for="item in toasts"
      :key="item.id"
      class="toast"
      :class="`toast--${item.tone}`"
      @click="dismissToast(item.id)"
    >
      {{ item.message }}
    </button>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  z-index: 200;
  top: 94px;
  left: 50%;
  display: grid;
  gap: 8px;
  width: min(420px, calc(100vw - 36px));
  transform: translateX(-50%);
}

.toast {
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--paper-soft);
  color: var(--ink);
  box-shadow: 0 10px 26px rgba(46, 42, 36, 0.12);
  font-size: 18px;
  text-align: left;
}

.toast--warning,
.toast--error {
  border-left: 3px solid var(--terracotta);
}

.toast--success {
  border-left: 3px solid var(--moss);
}
</style>
