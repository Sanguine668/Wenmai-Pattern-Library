<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
})
const emit = defineEmits(['select'])

const root = ref(null)
const width = ref(0)
const height = ref(0)
const path = ref('')
const columns = computed(() => {
  if (width.value >= 1060) return 5
  if (width.value >= 800) return 4
  if (width.value >= 540) return 3
  return 2
})

const rows = computed(() => {
  const size = columns.value
  const result = []
  for (let index = 0; index < props.items.length; index += size) {
    result.push({
      reverse: result.length % 2 === 1,
      items: props.items.slice(index, index + size),
    })
  }
  return result
})

let observer = null
let frame = 0

function scheduleDraw() {
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(() => nextTick(draw))
}

function draw() {
  const element = root.value
  if (!element) return
  const box = element.getBoundingClientRect()
  width.value = Math.round(box.width)
  height.value = Math.round(box.height)
  const entries = []
  element.querySelectorAll('.timeline-row').forEach((row) => {
    const dots = [...row.querySelectorAll('.timeline-dot')]
    for (const dot of dots) {
      const rect = dot.getBoundingClientRect()
      entries.push({
        dot,
        x: rect.left - box.left + rect.width / 2,
        y: rect.top - box.top + rect.height / 2,
      })
    }
  })
  if (!entries.length) {
    path.value = ''
    return
  }
  path.value = roundedPath(entries)
  shiftCornerDots(entries)
}

function shiftCornerDots(entries) {
  const points = entries.map(({ x, y }) => ({ x, y }))
  entries.forEach(({ dot }) => {
    dot.style.removeProperty('--dot-shift-x')
    dot.style.removeProperty('--dot-shift-y')
  })
  for (let index = 1; index < points.length - 1; index += 1) {
    const previous = points[index - 1]
    const current = points[index]
    const next = points[index + 1]
    const inLength = Math.hypot(current.x - previous.x, current.y - previous.y)
    const outLength = Math.hypot(next.x - current.x, next.y - current.y)
    if (!inLength || !outLength) continue
    const inX = (current.x - previous.x) / inLength
    const inY = (current.y - previous.y) / inLength
    const outX = (next.x - current.x) / outLength
    const outY = (next.y - current.y) / outLength
    if (inX * outX + inY * outY > 0.999) continue
    const cut = Math.min(30, inLength / 2, outLength / 2)
    entries[index].dot.style.setProperty('--dot-shift-x', `${(0.25 * cut * (outX - inX)).toFixed(1)}px`)
    entries[index].dot.style.setProperty('--dot-shift-y', `${(0.25 * cut * (outY - inY)).toFixed(1)}px`)
  }
}

function roundedPath(entries) {
  if (entries.length < 2) return ''
  const radius = 30
  const commands = [`M ${entries[0].x.toFixed(1)} ${entries[0].y.toFixed(1)}`]
  for (let index = 1; index < entries.length - 1; index += 1) {
    const previous = entries[index - 1]
    const current = entries[index]
    const next = entries[index + 1]
    const inLength = Math.hypot(current.x - previous.x, current.y - previous.y)
    const outLength = Math.hypot(next.x - current.x, next.y - current.y)
    if (!inLength || !outLength) {
      commands.push(`L ${current.x.toFixed(1)} ${current.y.toFixed(1)}`)
      continue
    }
    const inX = (current.x - previous.x) / inLength
    const inY = (current.y - previous.y) / inLength
    const outX = (next.x - current.x) / outLength
    const outY = (next.y - current.y) / outLength
    if (inX * outX + inY * outY > 0.999) {
      commands.push(`L ${current.x.toFixed(1)} ${current.y.toFixed(1)}`)
      continue
    }
    const cut = Math.min(radius, inLength / 2, outLength / 2)
    const fromX = current.x - inX * cut
    const fromY = current.y - inY * cut
    const toX = current.x + outX * cut
    const toY = current.y + outY * cut
    commands.push(
      `L ${fromX.toFixed(1)} ${fromY.toFixed(1)}`,
      `Q ${current.x.toFixed(1)} ${current.y.toFixed(1)} ${toX.toFixed(1)} ${toY.toFixed(1)}`,
    )
  }
  const last = entries[entries.length - 1]
  commands.push(`L ${last.x.toFixed(1)} ${last.y.toFixed(1)}`)
  return commands.join(' ')
}

onMounted(() => {
  observer = new ResizeObserver(scheduleDraw)
  observer.observe(root.value)
  window.addEventListener('resize', scheduleDraw)
  document.fonts?.ready.then(scheduleDraw)
  scheduleDraw()
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('resize', scheduleDraw)
  cancelAnimationFrame(frame)
})

watch(rows, scheduleDraw, { flush: 'post' })
</script>

<template>
  <div
    ref="root"
    class="timeline"
    :style="{ '--cols': columns }"
  >
    <svg
      class="timeline__axis"
      :viewBox="`0 0 ${Math.max(width, 1)} ${Math.max(height, 1)}`"
      aria-hidden="true"
    >
      <path v-if="path" :d="path" vector-effect="non-scaling-stroke" />
    </svg>
    <div
      v-for="(row, rowIndex) in rows"
      :key="rowIndex"
      class="timeline-row"
      :class="{ 'is-reverse': row.reverse }"
    >
      <button
        v-for="item in row.items"
        :key="item.label"
        type="button"
        class="timeline-item"
        :class="{ 'is-pending': item.pending }"
        :disabled="item.pending"
        :aria-label="item.pending ? `${item.label}，档案待补` : `查看 ${item.label} 的 ${item.count} 件纹样`"
        @click="emit('select', item.label)"
      >
        <span class="timeline-dot" aria-hidden="true"></span>
        <span class="timeline-heading">
          <strong>{{ item.label }}</strong>
          <span class="timeline-years">（{{ item.years ? item.years.replace('约', '') : '年代未定' }}）</span>
        </span>
        <small>{{ item.pending ? '档案待补' : `${item.count} 件样本` }}</small>
      </button>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  --axis: var(--accent-mid);
  --gap: 22px;
  --dot-color: #a86a3d;
  position: relative;
  padding-top: 8px;
}

.timeline__axis {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  color: var(--axis);
  pointer-events: none;
}

.timeline__axis path {
  fill: none;
  stroke: currentColor;
  stroke-width: 3.5;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.8;
}

.timeline-row {
  display: flex;
  justify-content: space-between;
  gap: var(--gap);
  padding-top: 32px;
}

.timeline-row + .timeline-row {
  margin-top: 20px;
}

.timeline-row.is-reverse {
  flex-direction: row-reverse;
}

.timeline-item {
  position: relative;
  display: grid;
  flex: 0 0 min(220px, calc((100% - (var(--cols) - 1) * var(--gap)) / var(--cols)));
  gap: 4px;
  align-content: start;
  min-height: 92px;
  padding: 0 4px 0 24px;
  border: 0;
  background: transparent;
  color: var(--ink);
  text-align: left;
  transition: color 0.3s var(--ease);
}

.timeline-item:hover strong {
  color: var(--accent-strong);
}

.timeline-item.is-pending {
  cursor: default;
}

.timeline-item.is-pending strong,
.timeline-item.is-pending small {
  color: var(--ink-mute);
}

.timeline-item.is-pending .timeline-dot {
  border: 3px solid var(--dot-color);
  background: transparent;
}

.timeline-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px;
}

.timeline-dot {
  position: absolute;
  top: -25px;
  left: 10px;
  box-sizing: border-box;
  width: 16px;
  height: 16px;
  border: 0;
  border-radius: 50%;
  background: var(--dot-color);
  transform: translate(var(--dot-shift-x, 0), var(--dot-shift-y, 0));
  transition: transform 0.3s var(--ease), background 0.3s var(--ease);
}

.timeline-item:hover .timeline-dot {
  background: var(--accent-strong);
  transform: translate(var(--dot-shift-x, 0), var(--dot-shift-y, 0)) scale(1.35);
}

.timeline-item strong {
  font-family: var(--serif);
  font-size: 24px;
  font-weight: 500;
  line-height: 1.2;
  transition: color 0.3s var(--ease);
}

.timeline-years {
  color: var(--ink-mute);
  font-size: 16px;
  line-height: 1.45;
  white-space: nowrap;
}

.timeline-item small {
  color: var(--ink-soft);
  font-size: 19px;
  letter-spacing: 0.02em;
}

@media (max-width: 700px) {
  .timeline {
    --gap: 14px;
  }

  .timeline-row {
    justify-content: flex-start;
    padding-top: 30px;
  }

  .timeline-item {
    max-width: none;
    flex: 0 0 calc((100% - var(--gap)) / 2);
    min-height: 84px;
    padding: 0 8px 0 24px;
  }

  .timeline-heading {
    flex-direction: column;
    align-items: flex-start;
    gap: 1px;
  }

  .timeline-item strong {
    font-size: 21px;
  }

  .timeline-dot {
    top: -22px;
    left: 8px;
  }
}
</style>
