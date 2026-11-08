<script setup>
import AppIcon from './AppIcon.vue'
import { useLibrary } from '../lib/library'

const props = defineProps({
  pattern: { type: Object, required: true },
  variant: { type: String, default: 'default' },
})
const emit = defineEmits(['click'])
const { isFavorite, toggleFavorite } = useLibrary()

function onFavorite(event) {
  event.stopPropagation()
  toggleFavorite(props.pattern.id)
}
</script>

<template>
  <article
    class="specimen"
    :class="`specimen--${variant}`"
    :data-pattern-id="pattern.id"
    @click="emit('click', pattern)"
  >
    <div class="specimen__image-wrap">
      <img
        v-if="pattern.image"
        :src="pattern.image"
        :alt="pattern.name"
        class="specimen__image"
        loading="lazy"
      />
      <div v-else class="specimen__no-image">
        <span>暂无图像</span>
      </div>
      <span class="catalogue-no specimen__catalogue">{{ pattern.catalog }}</span>
      <button
        class="specimen__favorite"
        :class="{ 'is-saved': isFavorite(pattern.id) }"
        :aria-label="isFavorite(pattern.id) ? '取消收藏' : '收藏纹样'"
        @click="onFavorite"
      >
        <AppIcon name="heart" :size="17" />
      </button>
    </div>
    <div class="specimen__body">
      <div class="specimen__eyebrow">
        <span>{{ pattern.motifEn }}</span>
        <span>{{ pattern.dynasty }}</span>
      </div>
      <h3 class="specimen__title">{{ pattern.name }}</h3>
      <div class="specimen__foot">
        <div class="specimen__tags">
          <span>{{ pattern.motifType }}</span>
          <span>{{ pattern.carrier }}</span>
        </div>
        <div class="specimen__thread" aria-hidden="true">
          <span
            v-for="color in pattern.colors"
            :key="color.hex"
            :style="{ background: color.hex }"
          />
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped>
.specimen {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(242, 241, 236, 0.74);
  color: var(--ink);
  cursor: pointer;
  transition: transform 0.45s var(--ease), box-shadow 0.45s var(--ease),
    border-color 0.45s var(--ease);
}

.specimen:hover {
  transform: translateY(-4px);
  border-color: var(--clay);
  box-shadow: var(--shadow-soft);
}

.specimen::before {
  position: absolute;
  z-index: 2;
  top: 0;
  right: 0;
  left: 0;
  height: 4px;
  background: var(--terracotta);
  content: "";
}

.specimen__image-wrap {
  position: relative;
  overflow: hidden;
  background: var(--paper-deep);
}

.specimen__image {
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: contain;
  padding: 10px;
  background: var(--paper-soft);
  transition: transform 0.7s var(--ease);
}

.specimen__no-image {
  display: grid;
  width: 100%;
  aspect-ratio: 4 / 5;
  place-items: center;
  background:
    linear-gradient(var(--line-soft) 1px, transparent 1px),
    linear-gradient(90deg, var(--line-soft) 1px, transparent 1px);
  background-color: var(--paper-soft);
  background-size: 24px 24px;
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.12em;
}

.specimen:hover .specimen__image {
  transform: scale(1.025);
}

.specimen__catalogue {
  position: absolute;
  top: 13px;
  left: 14px;
  padding: 4px 7px;
  background: rgba(232, 231, 225, 0.92);
  border-radius: 4px;
}

.specimen__favorite {
  position: absolute;
  top: 11px;
  right: 11px;
  display: grid;
  width: 31px;
  height: 31px;
  place-items: center;
  border: 1px solid rgba(232, 231, 225, 0.72);
  border-radius: 50%;
  background: rgba(21, 37, 40, 0.42);
  color: var(--paper-soft);
  transition: all 0.3s var(--ease);
}

.specimen__favorite:hover,
.specimen__favorite.is-saved {
  border-color: var(--terracotta);
  background: var(--terracotta);
  color: var(--paper-soft);
}

.specimen__body {
  padding: 16px 18px 18px;
}

.specimen__eyebrow {
  display: flex;
  justify-content: space-between;
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.04em;
}

.specimen__title {
  margin-top: 7px;
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.4;
}

.specimen__thread {
  display: flex;
  gap: 5px;
  align-items: center;
  margin-top: 0;
}

.specimen__thread span {
  width: 18px;
  height: 3px;
  border-radius: 99px;
}

.specimen__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.specimen__tags span {
  padding: 1px 7px;
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.45;
}

.specimen__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.specimen__meta {
  color: var(--ink-mute);
  font-size: 18px;
}

.specimen--large .specimen__image {
  aspect-ratio: 4 / 3.5;
}

.specimen--large .specimen__title {
  font-size: clamp(20px, 2.2vw, 27px);
}

@media (max-width: 700px) {
  .specimen__image {
    aspect-ratio: 4 / 4.4;
  }
}
</style>
