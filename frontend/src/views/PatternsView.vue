<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PatternCard from '../components/PatternCard.vue'
import {
  patterns as fallbackPatterns,
} from '../data/patterns'
import { OTHER_MOTIF, motifDisplayLabel, sortMotifs } from '../data/motifs'
import { apiAsset, apiFetch } from '../lib/api'
import { useMeta } from '../lib/meta'

const route = useRoute()
const router = useRouter()
const { motifs, dynasties: metaDynasties, carriers: metaCarriers, loadMeta } = useMeta()

const keyword = ref(route.query.keyword || '')
const motif = ref(route.query.motif || '')
const dynasty = ref(route.query.dynasty || '')
const carrier = ref(route.query.carrier || '')
const sort = ref(route.query.sort || 'curated')
const page = ref(Number(route.query.page) || 1)
const pageSize = 24
const items = ref(fallbackPatterns)
const total = ref(fallbackPatterns.length)
const loading = ref(true)
const apiConnected = ref(false)
const facets = ref(null)
let requestId = 0
let facetRequestId = 0
let facetKey = ''
const motifOptions = computed(() => sortMotifs(facets.value?.motifs || motifs.value))

const DYNASTY_ORDER = {
  新石器: 1, 商: 2, 周: 3, 秦: 4, 汉: 5, 三国: 6, 晋: 7, 南北朝: 8,
  隋: 9, 唐: 10, 五代: 11, 宋: 12, 辽: 13, 金: 14, 元: 15, 明: 16, 清: 17,
}

const dynasties = computed(() =>
  (facets.value?.dynasties || metaDynasties.value)
    .filter((item) => !['未知', '年代未定'].includes(item.label))
    .sort((a, b) => (DYNASTY_ORDER[a.label] || 99) - (DYNASTY_ORDER[b.label] || 99)),
)

const carrierOptions = computed(
  () => facets.value?.carriers || metaCarriers.value,
)

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const pageItems = computed(() => {
  const count = pageCount.value
  const current = page.value
  if (count <= 7) return Array.from({ length: count }, (_, index) => index + 1)
  const result = [1]
  const start = Math.max(2, current - 2)
  const end = Math.min(count - 1, current + 2)
  if (start > 2) result.push('ellipsis-start')
  for (let value = start; value <= end; value += 1) result.push(value)
  if (end < count - 1) result.push('ellipsis-end')
  result.push(count)
  return result
})

function fallbackFilter() {
  const q = keyword.value.trim().toLowerCase()
  let result = fallbackPatterns.filter((item) => {
    const matchesMotif = !motif.value || item.motifType === motif.value
    const matchesDynasty = !dynasty.value || item.dynasty === dynasty.value
    const matchesCarrier = !carrier.value || item.carrier === carrier.value
    const haystack = [
      item.name,
      item.originalTitle,
      item.motifType,
      item.secondary,
      item.dynasty,
      item.carrier,
      item.source,
    ].join(' ').toLowerCase()
    return matchesMotif && matchesDynasty && matchesCarrier && (!q || haystack.includes(q))
  })
  if (sort.value === 'dynasty') {
    result = [...result].sort((a, b) => (a.dynasty || '').localeCompare(b.dynasty || '', 'zh'))
  } else if (sort.value === 'title') {
    result = [...result].sort((a, b) => a.name.localeCompare(b.name, 'zh'))
  }
  items.value = result
  total.value = result.length
}

async function loadFacets() {
  const key = JSON.stringify([
    keyword.value.trim(),
    motif.value,
    dynasty.value,
    carrier.value,
  ])
  if (key === facetKey) return
  facetKey = key
  const current = ++facetRequestId
  const params = new URLSearchParams()
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
  if (motif.value) params.set('motif', motif.value)
  if (dynasty.value) params.set('dynasty', dynasty.value)
  if (carrier.value) params.set('carrier', carrier.value)
  try {
    const data = await apiFetch(`/api/facets?${params}`)
    if (current === facetRequestId) facets.value = data
  } catch {
    if (current === facetRequestId) facets.value = null
  }
}

async function loadPatterns() {
  const current = ++requestId
  loading.value = true
  loadFacets()
  const params = new URLSearchParams({
    limit: String(pageSize),
    offset: String((page.value - 1) * pageSize),
    sort: sort.value,
  })
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
  if (motif.value) params.set('motif', motif.value)
  if (dynasty.value) params.set('dynasty', dynasty.value)
  if (carrier.value) params.set('carrier', carrier.value)
  try {
    const data = await apiFetch(`/api/patterns?${params}`)
    if (current !== requestId) return
    items.value = data.items.map((item) => ({ ...item, image: apiAsset(item.image) }))
    total.value = data.total
    page.value = Math.min(page.value, Math.max(1, Math.ceil(data.total / pageSize)))
    apiConnected.value = true
  } catch {
    if (current !== requestId) return
    apiConnected.value = false
    page.value = 1
    fallbackFilter()
  } finally {
    if (current === requestId) {
      loading.value = false
      restoreReturnScroll()
    }
  }
}

const activeFilters = computed(() => [
  motif.value && { type: 'motif', label: motif.value },
  dynasty.value && { type: 'dynasty', label: dynasty.value },
  carrier.value && { type: 'carrier', label: carrier.value },
].filter(Boolean))

watch(
  () => route.query,
  (query) => {
    keyword.value = query.keyword || ''
    motif.value = query.motif || ''
    dynasty.value = query.dynasty || ''
    carrier.value = query.carrier || ''
    sort.value = query.sort || 'curated'
    page.value = Number(query.page) || 1
  },
)

function choose(type, value) {
  if (type === 'motif') motif.value = motif.value === value ? '' : value
  if (type === 'dynasty') dynasty.value = dynasty.value === value ? '' : value
  if (type === 'carrier') carrier.value = carrier.value === value ? '' : value
  page.value = 1
  syncQuery()
}

function syncQuery() {
  const query = {}
  if (keyword.value.trim()) query.keyword = keyword.value.trim()
  if (motif.value) query.motif = motif.value
  if (dynasty.value) query.dynasty = dynasty.value
  if (carrier.value) query.carrier = carrier.value
  if (sort.value !== 'curated') query.sort = sort.value
  if (page.value > 1) query.page = String(page.value)
  router.replace({ path: '/patterns', query })
  loadPatterns()
}

function clearFilters() {
  keyword.value = ''
  motif.value = ''
  dynasty.value = ''
  carrier.value = ''
  sort.value = 'curated'
  page.value = 1
  router.replace({ path: '/patterns' })
  loadPatterns()
}

function openPattern(pattern) {
  try {
    sessionStorage.setItem(
      'wenmai:patterns-return',
      JSON.stringify({ path: route.fullPath, y: window.scrollY, at: Date.now() }),
    )
  } catch {
    /* 忽略隐私模式下的存储异常 */
  }
  router.push(`/patterns/${pattern.id}`)
}

function restoreReturnScroll() {
  let saved = null
  try {
    saved = JSON.parse(sessionStorage.getItem('wenmai:patterns-return') || 'null')
  } catch {
    return
  }
  if (!saved || saved.path !== route.fullPath) return
  if (Date.now() - saved.at > 10 * 60 * 1000) {
    sessionStorage.removeItem('wenmai:patterns-return')
    return
  }
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      window.scrollTo({ top: saved.y, behavior: 'auto' })
      sessionStorage.removeItem('wenmai:patterns-return')
    })
  })
}

function changePage(nextPage) {
  page.value = Math.min(Math.max(1, nextPage), pageCount.value)
  syncQuery()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  loadMeta()
  loadPatterns()
})</script>

<template>
  <div class="page patterns-page">
    <div class="container">
      <header class="page-head">
        <div>
          <p class="page-kicker">LIBRARY / 纹样总目</p>
          <h1 class="page-title">纹样库</h1>
        </div>
        <p class="page-subtitle">
          当前显示 {{ total }} 条纹样档案，可按纹样类型、朝代和载体组合检索。
          图片与元数据均由资源数据库实时返回。
        </p>
      </header>

      <div class="library-layout">
        <aside class="filter-rail">
          <div class="filter-rail__head">
            <span class="eyebrow">FILTER / 筛选</span>
            <button v-if="activeFilters.length || keyword" class="text-link" @click="clearFilters">
              清空
            </button>
          </div>

          <label class="search-line">
            <AppIcon name="search" :size="16" />
            <input
              v-model="keyword"
              type="search"
              placeholder="名称、描述或来源"
              @change="syncQuery"
              @keyup.enter="syncQuery"
            />
          </label>

          <div class="filter-group">
            <span class="filter-group__label">纹样类型</span>
            <div class="filter-list">
              <button
                v-for="item in motifOptions"
                :key="item.label"
                class="filter-option"
                :class="{
                  'is-active': motif === item.label,
                  'is-residual': item.label === OTHER_MOTIF,
                }"
                @click="choose('motif', item.label)"
              >
                <span>{{ motifDisplayLabel(item.label) }}</span>
                <small>{{ item.count }}</small>
              </button>
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-group__label">朝代</span>
            <div class="filter-list filter-list--inline">
              <button
                v-for="item in dynasties"
                :key="item.label"
                class="filter-option"
                :class="{ 'is-active': dynasty === item.label }"
                @click="choose('dynasty', item.label)"
              >
                <span>{{ item.label }}</span>
                <small>{{ item.count }}</small>
              </button>
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-group__label">文物载体</span>
            <div class="filter-list filter-list--inline">
              <button
                v-for="item in carrierOptions"
                :key="item.label"
                class="filter-option"
                :class="{ 'is-active': carrier === item.label }"
                @click="choose('carrier', item.label)"
              >
                <span>{{ item.label }}</span>
                <small>{{ item.count }}</small>
              </button>
            </div>
          </div>
        </aside>

        <section class="library-main">
          <div class="library-toolbar">
            <div>
              <strong>{{ total }}</strong>
              <span> 条档案</span>
              <span v-if="activeFilters.length" class="library-toolbar__filters">
                ·
                <button
                  v-for="item in activeFilters"
                  :key="item.type"
                  class="active-filter"
                  @click="choose(item.type, item.label)"
                >
                  {{ item.label }} ×
                </button>
              </span>
            </div>
            <label class="sort-control">
              <span>排序</span>
              <select v-model="sort" @change="page = 1; syncQuery()">
                <option value="curated">编目顺序</option>
                <option value="dynasty">朝代</option>
                <option value="title">名称</option>
              </select>
            </label>
          </div>

          <div v-if="loading" class="library-loading">
            <span class="eyebrow">LOADING</span>
            <p>正在读取资源数据库…</p>
          </div>
          <div v-else-if="items.length" class="library-grid">
            <PatternCard
              v-for="pattern in items"
              :key="pattern.id"
              :pattern="pattern"
              @click="openPattern"
            />
          </div>
          <div v-else class="empty-state">
            <p class="eyebrow">NO ENTRY</p>
            <h2>没有匹配的纹样</h2>
            <p>换一个类别，或清除当前筛选条件。</p>
            <button class="btn" @click="clearFilters">清空筛选</button>
          </div>

          <nav v-if="!loading && total > pageSize" class="pagination" aria-label="纹样分页">
            <button
              class="pagination__step"
              :disabled="page <= 1"
              @click="changePage(page - 1)"
            >
              上一页
            </button>
            <div class="pagination__pages">
              <template v-for="item in pageItems" :key="item">
                <span v-if="typeof item === 'string'" class="pagination__ellipsis">…</span>
                <button
                  v-else
                  class="pagination__page"
                  :class="{ 'is-active': item === page }"
                  :aria-current="item === page ? 'page' : undefined"
                  @click="changePage(item)"
                >
                  {{ item }}
                </button>
              </template>
            </div>
            <button
              class="pagination__step"
              :disabled="page >= pageCount"
              @click="changePage(page + 1)"
            >
              下一页
            </button>
            <span class="pagination__summary">共 {{ pageCount }} 页</span>
          </nav>
          <p class="connection-note">
            {{ apiConnected ? '数据库已连接 · 全量分页显示' : '数据库未连接 · 当前显示 54 条内置样本' }}
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.patterns-page {
  padding-top: 42px;
}

.library-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 48px;
  align-items: start;
}

.filter-rail {
  position: sticky;
  top: 112px;
  max-height: calc(100vh - 136px);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-top: 16px;
  padding-bottom: 22px;
  padding-right: 26px;
  border-top: 4px solid var(--terracotta);
  border-right: 1px solid var(--line);
  scrollbar-width: thin;
  scrollbar-color: var(--line) transparent;
}

.filter-rail::-webkit-scrollbar {
  width: 6px;
}

.filter-rail::-webkit-scrollbar-thumb {
  border-radius: 99px;
  background: var(--line);
}

.filter-rail__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--line);
}

.filter-rail__head .text-link {
  font-size: 18px;
}

.search-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 0;
  border-bottom: 1px solid var(--line-soft);
  color: var(--ink-mute);
}

.search-line input {
  min-width: 0;
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--ink);
  font-size: 18px;
  outline: none;
}

.search-line input::placeholder {
  color: var(--ink-mute);
}

.filter-group {
  padding: 18px 0;
  border-bottom: 1px solid var(--line-soft);
}

.filter-group__label {
  display: block;
  margin-bottom: 10px;
  color: var(--terracotta);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.filter-list {
  display: grid;
  gap: 2px;
}

.filter-list--inline {
  grid-template-columns: 1fr 1fr;
  column-gap: 20px;
  row-gap: 2px;
}

.filter-option {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 4px 0;
  border: 0;
  background: transparent;
  color: var(--ink-soft);
  text-align: left;
  font-size: 18px;
  transition: color 0.25s var(--ease), padding-left 0.25s var(--ease);
}

.filter-option small {
  color: var(--ink-mute);
  font-size: 18px;
}

.filter-option:hover,
.filter-option.is-active {
  padding-left: 5px;
  color: var(--terracotta);
}

.filter-option.is-residual {
  margin-top: 6px;
  border-top: 1px dashed var(--line-soft);
  padding-top: 9px;
  color: var(--ink-mute);
}

.filter-option.is-residual small {
  color: var(--ink-mute);
}

.filter-option.is-active {
  padding-left: 8px;
  border-left: 3px solid var(--terracotta);
  background: rgba(49, 87, 97, 0.12);
}

.filter-option.is-active small {
  color: var(--terracotta);
}

.library-toolbar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 18px;
  min-height: 34px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
  color: var(--ink-soft);
  font-size: 18px;
}

.library-toolbar strong {
  color: var(--terracotta);
  font-family: var(--serif);
  font-size: 24px;
  font-weight: 500;
}

.library-toolbar__filters {
  color: var(--ink-mute);
}

.active-filter {
  border: 0;
  background: transparent;
  color: var(--terracotta);
  font-size: 18px;
}

.sort-control {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-mute);
  font-size: 18px;
}

.sort-control select {
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--ink-soft);
  font-size: 18px;
  outline: none;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  padding-top: 22px;
}

.empty-state {
  display: grid;
  justify-items: center;
  gap: 9px;
  padding: 94px 20px;
  text-align: center;
}

.empty-state h2 {
  font-family: var(--serif);
  font-size: 25px;
  font-weight: 500;
}

.empty-state p:not(.eyebrow) {
  color: var(--ink-mute);
  font-size: 18px;
}

.empty-state .btn {
  margin-top: 10px;
}

.library-loading {
  display: grid;
  min-height: 280px;
  place-content: center;
  gap: 8px;
  color: var(--ink-mute);
  text-align: center;
}

.pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding-top: 30px;
}

.pagination__pages {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.pagination button {
  min-width: 42px;
  min-height: 42px;
  padding: 5px 13px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: transparent;
  color: var(--ink-soft);
  font-size: 18px;
  transition: border-color 0.25s var(--ease), background 0.25s var(--ease),
    color 0.25s var(--ease);
}

.pagination button:hover:not(:disabled) {
  border-color: var(--terracotta);
  color: var(--terracotta);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.pagination__page.is-active {
  border-color: var(--terracotta);
  background: var(--terracotta);
  color: var(--paper-soft);
  font-weight: 600;
}

.pagination__ellipsis {
  padding: 0 2px;
  color: var(--ink-mute);
  font-size: 18px;
}

.pagination__summary,
.connection-note {
  color: var(--ink-mute);
  font-size: 18px;
}

.pagination__summary {
  margin-left: 6px;
}

.connection-note {
  padding-top: 14px;
  text-align: center;
}

@media (max-width: 1060px) {
  .library-layout {
    grid-template-columns: 260px minmax(0, 1fr);
    gap: 28px;
  }

  .library-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .library-layout {
    grid-template-columns: 1fr;
  }

  .filter-rail {
    position: static;
    max-height: none;
    overflow: visible;
    padding-right: 0;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .filter-list--inline {
    grid-template-columns: repeat(3, 1fr);
  }

  .library-grid {
    gap: 14px;
  }
}

@media (max-width: 520px) {
  .library-grid {
    grid-template-columns: 1fr;
  }
}
</style>
