<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PatternCard from '../components/PatternCard.vue'
import { patterns as fallbackPatterns } from '../data/patterns'
import { apiAsset, apiFetch } from '../lib/api'
import { useLibrary } from '../lib/library'

const route = useRoute()
const router = useRouter()
const lightbox = ref(false)
const loading = ref(true)
const pattern = ref(null)
const related = ref([])
const activeImage = ref('')
const { isFavorite, toggleFavorite, recordView } = useLibrary()

const displayImage = computed(() => activeImage.value || pattern.value?.image || '')

function fallbackRelated(current) {
  return fallbackPatterns
    .filter(
      (item) =>
        item.id !== current.id &&
        (item.motifType === current.motifType ||
          item.dynasty === current.dynasty ||
          item.carrier === current.carrier),
    )
    .slice(0, 4)
}

function withAssets(item) {
  return {
    ...item,
    image: apiAsset(item.image),
    images: (item.images || []).map(apiAsset),
  }
}

async function loadPattern() {
  const id = String(route.params.id)
  loading.value = true
  try {
    const data = await apiFetch(`/api/patterns/${encodeURIComponent(id)}`)
    pattern.value = withAssets(data)
    related.value = (data.related || []).map(withAssets)
    activeImage.value = pattern.value.image
  } catch {
    const current = fallbackPatterns.find((item) => item.id === id) || null
    pattern.value = current
    related.value = current ? fallbackRelated(current) : []
    activeImage.value = current?.image || ''
  } finally {
    loading.value = false
    remember()
  }
}

function remember() {
  if (pattern.value) recordView(pattern.value.id)
}

onMounted(loadPattern)
watch(() => route.params.id, loadPattern)

function openRelated(item) {
  router.push(`/patterns/${item.id}`)
}

function goBackToList() {
  let target = '/patterns'
  try {
    const saved = JSON.parse(sessionStorage.getItem('wenmai:patterns-return') || 'null')
    if (saved?.path) target = saved.path
  } catch {
    /* 忽略隐私模式下的存储异常 */
  }
  router.push(target)
}
</script>

<template>
  <div v-if="loading" class="page container detail-loading">
    <p class="eyebrow">LOADING</p>
    <p>正在读取纹样档案…</p>
  </div>

  <div class="page detail-page" v-else-if="pattern">
    <div class="container">
      <div class="detail-topline">
        <a href="/patterns" class="text-link" @click.prevent="goBackToList">
          <AppIcon name="arrow" :size="14" class="back-arrow" /> 返回纹样总目
        </a>
        <span class="catalogue-no">{{ pattern.catalog }}</span>
      </div>

      <article class="detail-grid">
        <div class="detail-visual">
          <button v-if="displayImage" class="detail-image" @click="lightbox = true">
            <img :src="displayImage" :alt="pattern.name" />
            <span class="detail-image__zoom">点击查看原图</span>
          </button>
          <div v-else class="detail-no-image">该档案暂无本地图片</div>
          <div v-if="pattern.images?.length > 1" class="detail-thumbs">
            <button
              v-for="(image, index) in pattern.images"
              :key="image"
              :class="{ 'is-active': displayImage === image }"
              :aria-label="`查看第 ${index + 1} 张图片`"
              @click="activeImage = image"
            >
              <img :src="image" :alt="`${pattern.name} 图片 ${index + 1}`" loading="lazy" />
            </button>
          </div>
          <div class="color-strip">
            <span class="eyebrow">PALETTE / 提取主色</span>
            <div class="color-strip__row">
              <div v-for="color in pattern.colors" :key="color.hex" class="color-cell">
                <span class="color-cell__swatch" :style="{ background: color.hex }"></span>
                <span>{{ color.name }}</span>
                <small>{{ color.hex }}</small>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-copy">
          <p class="eyebrow">{{ pattern.motifEn }} · {{ pattern.source }}</p>
          <h1>{{ pattern.name }}</h1>
          <p v-if="pattern.originalTitle && pattern.originalTitle !== pattern.name" class="detail-original">
            {{ pattern.originalTitle }}
          </p>

          <div class="chip-row detail-chips">
            <span class="chip">{{ pattern.motifType }}</span>
            <span v-if="pattern.secondary" class="chip chip--muted">{{ pattern.secondary }}</span>
            <span class="chip chip--muted">{{ pattern.dynasty }}</span>
            <span class="chip chip--muted">{{ pattern.carrier }}</span>
          </div>

          <div class="detail-actions">
            <button
              class="btn"
              :class="{ 'btn--primary': isFavorite(pattern.id) }"
              @click="toggleFavorite(pattern.id)"
            >
              <AppIcon name="heart" :size="16" />
              {{ isFavorite(pattern.id) ? '已收藏' : '收藏此纹样' }}
            </button>
            <a
              v-if="pattern.sourceUrl"
              :href="pattern.sourceUrl"
              target="_blank"
              rel="noreferrer"
              class="btn btn--quiet"
            >
              查看来源 <AppIcon name="external" :size="15" />
            </a>
          </div>

          <dl class="archive-list">
            <div class="archive-item">
              <dt>年代</dt>
              <dd>
                <strong>{{ pattern.dynasty }}</strong>
                <small>{{ pattern.dateText || '来源记录未提供年代描述' }}</small>
              </dd>
            </div>
            <div class="archive-item">
              <dt>载体</dt>
              <dd>
                <strong>{{ pattern.carrier }}</strong>
                <small>器物表面纹样</small>
              </dd>
            </div>
            <div class="archive-item">
              <dt>收藏机构</dt>
              <dd>
                <strong>{{ pattern.source }}</strong>
                <small>{{ pattern.license }}</small>
              </dd>
            </div>
            <div class="archive-item">
              <dt>编目</dt>
              <dd>
                <strong>{{ pattern.catalog }}</strong>
                <small>纹样类型：{{ pattern.motifType }}</small>
              </dd>
            </div>
          </dl>

          <section class="detail-section">
            <div class="detail-section__head">
              <h2>纹样说明</h2>
              <span class="eyebrow">DESCRIPTION</span>
            </div>
            <p>{{ pattern.description }}</p>
          </section>

          <section class="detail-section detail-section--source">
            <div class="detail-section__head">
              <h2>档案来源</h2>
              <span class="eyebrow">PROVENANCE</span>
            </div>
            <p>
              本记录整理自 {{ pattern.source }} 的开放数据，保留原始编号、来源链接和许可信息。
              页面中的分类标签来自课程标注结果，纹样说明沿用来源描述。
            </p>
          </section>
        </div>
      </article>

      <section class="related-section" v-if="related.length">
        <div class="section-head">
          <div>
            <p class="eyebrow">SAME THREAD / 同类</p>
            <h2 class="section-title">沿同一谱系继续看</h2>
          </div>
          <RouterLink to="/patterns" class="text-link">回到总目 <AppIcon name="arrow" :size="14" /></RouterLink>
        </div>
        <div class="related-grid">
          <PatternCard
            v-for="item in related"
            :key="item.id"
            :pattern="item"
            @click="openRelated"
          />
        </div>
      </section>
    </div>

    <div v-if="lightbox" class="lightbox" @click.self="lightbox = false">
      <button class="lightbox__close" aria-label="关闭大图" @click="lightbox = false">
        <AppIcon name="close" :size="22" />
      </button>
      <img :src="displayImage" :alt="pattern.name" />
      <p>{{ pattern.catalog }} · {{ pattern.name }}</p>
    </div>
  </div>

  <div v-else class="page container missing">
    <p class="eyebrow">NOT FOUND</p>
    <h1>这条纹样暂时不在样本中</h1>
    <RouterLink to="/patterns" class="btn">返回纹样库</RouterLink>
  </div>
</template>

<style scoped>
.detail-page {
  padding-top: 34px;
}

.detail-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 17px;
  border-bottom: 1px solid var(--line);
}

.back-arrow {
  transform: rotate(180deg);
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  gap: clamp(40px, 7vw, 100px);
  padding-top: 38px;
}

.detail-visual {
  min-width: 0;
}

.detail-image {
  position: relative;
  display: block;
  width: 100%;
  padding: 14px;
  overflow: hidden;
  border: 0;
  border-radius: 24px;
  background: var(--moss-deep);
}

.detail-image img {
  width: 100%;
  max-height: 720px;
  object-fit: contain;
  background: var(--paper-soft);
  border-radius: 12px;
  transition: transform 0.8s var(--ease);
}

.detail-image:hover img {
  transform: scale(1.012);
}

.detail-image__zoom {
  position: absolute;
  right: 14px;
  bottom: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(232, 231, 225, 0.92);
  color: var(--ink-soft);
  font-size: 18px;
}

.detail-no-image {
  display: grid;
  min-height: 520px;
  place-items: center;
  border: 1px solid var(--line);
  background:
    linear-gradient(var(--line-soft) 1px, transparent 1px),
    linear-gradient(90deg, var(--line-soft) 1px, transparent 1px);
  background-color: var(--paper-soft);
  background-size: 28px 28px;
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.1em;
}

.detail-thumbs {
  display: flex;
  gap: 9px;
  margin-top: 12px;
  overflow-x: auto;
}

.detail-thumbs button {
  flex: 0 0 72px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--paper-soft);
}

.detail-thumbs button.is-active {
  border-color: var(--accent-strong);
}

.detail-thumbs img {
  width: 64px;
  height: 64px;
  object-fit: cover;
}

.detail-loading {
  display: grid;
  min-height: 50vh;
  place-content: center;
  color: var(--ink-mute);
  text-align: center;
}

.color-strip {
  display: grid;
  gap: 12px;
  margin-top: 19px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(175, 195, 198, 0.2);
}

.color-strip__row {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.color-cell {
  display: grid;
  grid-template-columns: 18px auto;
  column-gap: 7px;
  align-items: center;
  color: var(--ink-soft);
  font-size: 18px;
}

.color-cell small {
  grid-column: 2;
  color: var(--ink-mute);
  font-size: 18px;
}

.color-cell__swatch {
  grid-row: span 2;
  width: 18px;
  height: 26px;
  border-radius: 3px;
}

.detail-copy {
  padding-top: 9px;
  padding-left: 28px;
  border-left: 4px solid var(--terracotta);
}

.detail-copy h1 {
  margin-top: 13px;
  font-family: var(--serif);
  font-size: clamp(34px, 4vw, 48px);
  font-weight: 600;
  line-height: 1.2;
}

.detail-original {
  margin-top: 8px;
  color: var(--ink-mute);
  font-size: 18px;
}

.detail-chips {
  margin-top: 22px;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 22px 0;
  border-bottom: 1px solid var(--line);
}

.archive-list {
  margin: 0;
  padding: 6px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.archive-item {
  display: grid;
  grid-template-columns: 128px minmax(0, 1fr);
  gap: 16px;
  align-items: baseline;
  padding: 13px 0;
  border-bottom: 1px solid var(--line-soft);
}

.archive-item:last-child {
  border-bottom: 0;
}

.archive-item dt {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.archive-item dd {
  display: grid;
  gap: 3px;
  margin: 0;
}

.archive-item strong {
  color: var(--moss-deep);
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 500;
  line-height: 1.35;
}

.archive-item small {
  color: var(--ink-mute);
  font-size: 18px;
  line-height: 1.6;
}

.detail-section {
  padding: 25px 0;
  border-bottom: 1px solid var(--line);
}

.detail-section--source {
  border-bottom: 0;
}

.detail-section__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 11px;
}

.detail-section h2 {
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 600;
}

.detail-section p {
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.95;
}

.related-section {
  padding-top: 82px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.lightbox {
  position: fixed;
  z-index: 150;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 40px;
  background: rgba(46, 42, 36, 0.88);
}

.lightbox img {
  max-width: min(1100px, 88vw);
  max-height: 80vh;
  object-fit: contain;
}

.lightbox p {
  margin-top: 12px;
  color: var(--paper-soft);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.lightbox__close {
  position: fixed;
  top: 24px;
  right: 28px;
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border: 1px solid rgba(242, 241, 236, 0.56);
  border-radius: 50%;
  background: transparent;
  color: var(--paper-soft);
}

.missing {
  display: grid;
  justify-items: start;
  align-content: center;
  gap: 14px;
}

.missing h1 {
  font-family: var(--serif);
  font-size: 34px;
  font-weight: 500;
}

@media (max-width: 980px) {
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 35px;
  }

  .related-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .related-grid {
    grid-template-columns: 1fr;
  }

  .archive-item {
    grid-template-columns: 96px minmax(0, 1fr);
    gap: 12px;
  }
}
</style>
