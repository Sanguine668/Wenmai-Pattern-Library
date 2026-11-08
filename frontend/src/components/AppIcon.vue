<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'search'">
      <circle cx="10.8" cy="10.8" r="6.4" />
      <path d="m15.6 15.6 4.2 4.2" />
    </template>
    <template v-else-if="name === 'heart'">
      <path d="M20.4 5.7a5 5 0 0 0-7.1 0L12 7l-1.3-1.3a5 5 0 0 0-7.1 7.1L12 21l8.4-8.2a5 5 0 0 0 0-7.1Z" />
    </template>
    <template v-else-if="name === 'arrow'">
      <path d="M4 12h15" />
      <path d="m13 6 6 6-6 6" />
    </template>
    <template v-else-if="name === 'upload'">
      <path d="M12 16V4" />
      <path d="m7 9 5-5 5 5" />
      <path d="M4 16v3h16v-3" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="m5 5 14 14M19 5 5 19" />
    </template>
    <template v-else-if="name === 'chat'">
      <path d="M4 5.5h16v11H9l-5 4v-15Z" />
      <path d="M8 10h8M8 13h5" />
    </template>
    <template v-else-if="name === 'book'">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" />
      <path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20" />
    </template>
    <template v-else-if="name === 'external'">
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" />
    </template>
    <template v-else-if="name === 'check'">
      <path d="m5 12 4.5 4.5L19 7" />
    </template>
    <template v-else-if="name === 'menu'">
      <path d="M4 7h16M4 12h16M4 17h16" />
    </template>
    <template v-else-if="name === 'grid'">
      <rect x="4" y="4" width="6" height="6" />
      <rect x="14" y="4" width="6" height="6" />
      <rect x="4" y="14" width="6" height="6" />
      <rect x="14" y="14" width="6" height="6" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="8" />
    </template>
  </svg>
</template>
