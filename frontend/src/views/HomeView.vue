<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PatternCard from '../components/PatternCard.vue'
import DynastyTimeline from '../components/DynastyTimeline.vue'
import {
  patterns,
  heroPanel,
} from '../data/patterns'
import { useLibraryStats } from '../lib/stats'
import { useMeta } from '../lib/meta'
import { OTHER_MOTIF } from '../data/motifs'

const { stats } = useLibraryStats()
const {
  motifs,
  dynasties: metaDynasties,
  carriers,
  metaConnected,
  loadMeta,
} = useMeta()
const indexMotifs = computed(() =>
  motifs.value.filter((item) => item.label !== OTHER_MOTIF),
)
const otherMotifCount = computed(
  () => motifs.value.find((item) => item.label === OTHER_MOTIF)?.count || 0,
)

const router = useRouter()
const query = ref('')
const featureRail = ref(null)
let featureTimer = null

const DYNASTY_META = {
  新石器: { order: 1, years: '约前8000—前2000' },
  商: { order: 2, years: '前1600—前1046' },
  周: { order: 3, years: '前1046—前256' },
  秦: { order: 4, years: '前221—前206' },
  汉: { order: 5, years: '前202—220' },
  三国: { order: 6, years: '220—280' },
  晋: { order: 7, years: '265—420' },
  南北朝: { order: 8, years: '420—589' },
  隋: { order: 9, years: '581—618' },
  唐: { order: 10, years: '618—907' },
  五代: { order: 11, years: '907—960' },
  宋: { order: 12, years: '960—1279' },
  辽: { order: 13, years: '907—1125' },
  金: { order: 14, years: '1115—1234' },
  元: { order: 15, years: '1271—1368' },
  明: { order: 16, years: '1368—1644' },
  清: { order: 17, years: '1644—1912' },
}

const heroIndex = ref(0)

const recommended = computed(() => {
  const picks = []
  const add = (item) => {
    if (item && item.image && !picks.some((pick) => pick.id === item.id)) picks.push(item)
  }
  add(patterns.find((item) => item.id === 'cleveland-101142'))
  add(patterns.find((item) => item.id === 'cleveland-119906'))
  add(heroPanel)
  add(patterns.find((item) => item.motifType === '花卉纹' && item.carrier === '织物'))
  add(patterns.find((item) => item.motifType === '龙纹'))
  add(patterns.find((item) => item.motifType === '凤纹'))
  for (const item of patterns) {
    if (picks.length >= 3) break
    add(item)
  }
  return picks.slice(0, 3)
})

const hero = computed(
  () => recommended.value[heroIndex.value] || recommended.value[0] || patterns[0],
)

function cardClass(index) {
  const total = recommended.value.length
  const offset = (index - heroIndex.value + total) % total
  return {
    'is-active': offset === 0,
    'is-behind-1': offset === 1,
    'is-behind-2': offset === 2,
  }
}

function handleHeroCard(index) {
  if (index === heroIndex.value) openPattern(recommended.value[index])
  else heroIndex.value = index
}

function cycleHero(step) {
  const total = recommended.value.length
  if (!total) return
  heroIndex.value = (heroIndex.value + step + total) % total
}

const featured = computed(() => {
  const seen = new Set()
  const result = []
  for (const item of patterns) {
    if (!seen.has(item.motifType)) {
      seen.add(item.motifType)
      result.push(item)
    }
    if (result.length === 5) break
  }
  return result
})

const recent = computed(() => patterns.slice(-5).reverse())

const dynasties = computed(() => {
  const list = metaDynasties.value
    .filter((item) => !['未知', '年代未定'].includes(item.label))
    .map((item) => ({ ...item, ...(DYNASTY_META[item.label] || {}) }))
    .sort((a, b) => (a.order || 99) - (b.order || 99))
  if (!list.some((item) => item.label === '近现代')) {
    list.push({
      label: '近现代',
      years: '1912 至今',
      count: null,
      pending: true,
    })
  }
  return list
})

function goFilter(type, value) {
  const query = {}
  if (value) query[type] = value
  router.push({ path: '/patterns', query })
}

function submitSearch() {
  const keyword = query.value.trim()
  if (keyword) router.push({ path: '/patterns', query: { keyword } })
}

function openPattern(pattern) {
  router.push(`/patterns/${pattern.id}`)
}

function scrollFeature(direction) {
  const rail = featureRail.value
  if (!rail) return
  rail.scrollBy({
    left: direction * Math.min(520, rail.clientWidth * 0.78),
    behavior: 'smooth',
  })
}

function stopAutoPlay() {
  if (featureTimer) window.clearInterval(featureTimer)
  featureTimer = null
}

function startAutoPlay() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  stopAutoPlay()
  featureTimer = window.setInterval(() => {
    const rail = featureRail.value
    if (!rail) return
    if (rail.scrollLeft + rail.clientWidth >= rail.scrollWidth - 8) {
      rail.scrollTo({ left: 0, behavior: 'smooth' })
    } else {
      scrollFeature(1)
    }
  }, 6000)
}

onMounted(() => {
  startAutoPlay()
  loadMeta()
})
onBeforeUnmount(stopAutoPlay)
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="container hero__grid">
        <div class="hero__copy">
          <p class="eyebrow">中华纹脉 · 中国传统纹样档案</p>
          <h1>沿器物的表面，<br /><em>读一条纹样的来路。</em></h1>
          <p class="hero__intro">
            从瓷器、织锦、漆器与拓片中整理纹样，以类别、朝代与载体编目。
            这里收录的不只是图像，还有它们来自哪件器物、哪一段年代。
          </p>
          <form class="hero-search" @submit.prevent="submitSearch">
            <AppIcon name="search" :size="18" />
            <input v-model="query" type="search" placeholder="检索纹样、朝代或载体" aria-label="检索纹样" />
            <button type="submit" class="hero-search__submit">检索</button>
          </form>
          <div class="hero__numbers">
            <div><strong>{{ stats.total }}</strong><span>档案记录</span></div>
          </div>
        </div>

        <figure class="hero__plate">
          <p class="hero__plate-kicker">为你推荐</p>
          <div class="hero__stack">
            <div
              v-for="(item, index) in recommended"
              :key="item.id"
              class="hero__card"
              :class="cardClass(index)"
              :aria-hidden="index !== heroIndex"
              @click="handleHeroCard(index)"
            >
              <div class="hero__plate-image">
                <img :src="item.image" :alt="index === heroIndex ? item.name : ''" />
              </div>
            </div>
          </div>
          <figcaption>
            <span class="catalogue-no">{{ hero.catalog }}</span>
            <span class="hero__caption-name">{{ hero.name }}</span>
            <span class="hero__caption-tags">
              <span>{{ hero.carrier }}</span>
              <span>{{ hero.dynasty }}</span>
            </span>
            <div class="hero__swatches" aria-label="纹样主色">
              <span
                v-for="color in hero.colors"
                :key="color.hex"
                :style="{ background: color.hex }"
                :title="color.name"
              ></span>
            </div>
          </figcaption>
          <div class="hero__stack-nav" aria-label="切换推荐图版">
            <button
              type="button"
              class="hero__nav-arrow hero__nav-arrow--prev"
              aria-label="上一张推荐"
              @click="cycleHero(-1)"
            >
              <AppIcon name="arrow" :size="15" />
            </button>
            <button
              v-for="(item, index) in recommended"
              :key="item.id"
              type="button"
              class="hero__dot"
              :class="{ 'is-active': index === heroIndex }"
              :aria-label="`查看推荐图版 ${index + 1}：${item.name}`"
              @click="heroIndex = index"
            ></button>
            <button
              type="button"
              class="hero__nav-arrow"
              aria-label="下一张推荐"
              @click="cycleHero(1)"
            >
              <AppIcon name="arrow" :size="15" />
            </button>
          </div>
        </figure>
      </div>
      <div class="hero__rule" aria-hidden="true"></div>
    </section>

    <section class="container index-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">CATALOGUE INDEX / 01</p>
          <h2 class="section-title">纹样总目</h2>
        </div>
        <RouterLink to="/patterns" class="text-link">浏览全部 <AppIcon name="arrow" :size="14" /></RouterLink>
      </div>
      <div class="index-grid">
        <button
          v-for="(item, index) in indexMotifs"
          :key="item.label"
          class="index-item"
          @click="goFilter('motif', item.label)"
        >
          <span class="index-item__thumb">
            <img v-if="item.image" :src="item.image" :alt="item.label" loading="lazy" />
          </span>
          <span class="index-item__title">
            <span class="index-item__no">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="index-item__name">{{ item.label }}</span>
          </span>
          <span class="index-item__en">{{ item.en }}</span>
          <span class="index-item__count">{{ item.count }}</span>
        </button>
      </div>
      <p class="index-footnote">
        另有
        <RouterLink
          :to="{ path: '/patterns', query: { motif: OTHER_MOTIF } }"
          class="text-link"
        >{{ otherMotifCount }} 条未归类档案</RouterLink>待复核，可单独筛选。
        {{ metaConnected ? '计数来自资源数据库实时统计。' : '数据库未连接，暂时显示内置样本计数。' }}
      </p>
    </section>

    <section class="container feature-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">SELECTED PLATES / 02</p>
          <h2 class="section-title">馆藏精选</h2>
        </div>
        <span class="section-note">按纹样类型每组取一例</span>
      </div>
      <div class="feature-carousel" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
        <div ref="featureRail" class="feature-rail">
          <PatternCard
            v-for="pattern in featured"
            :key="pattern.id"
            :pattern="pattern"
            @click="openPattern"
          />
        </div>
        <div class="feature-controls">
          <span>横向展播 · {{ featured.length }} 件精选</span>
          <div>
            <button aria-label="向前浏览" @click="scrollFeature(-1)">
              <AppIcon name="arrow" :size="18" class="control-prev" />
            </button>
            <button aria-label="向后浏览" @click="scrollFeature(1)">
              <AppIcon name="arrow" :size="18" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="dynasty-section">
      <div class="container">
        <div class="section-head">
          <div>
            <p class="eyebrow">BY DYNASTY / 03</p>
            <h2 class="section-title">按朝代展开</h2>
          </div>
          <div class="dynasty-actions">
            <span class="section-note">以记录中的年代标记归档</span>
            <button type="button" class="dynasty-all" @click="goFilter('dynasty', '')">
              全部朝代 <AppIcon name="arrow" :size="14" />
            </button>
          </div>
        </div>
        <DynastyTimeline
          :items="dynasties"
          @select="(label) => goFilter('dynasty', label)"
        />
      </div>
    </section>

    <section class="container recent-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">RECENT ENTRIES / 04</p>
          <h2 class="section-title">最近整理</h2>
        </div>
        <RouterLink to="/patterns" class="text-link">进入纹样库 <AppIcon name="arrow" :size="14" /></RouterLink>
      </div>
      <div class="recent-list">
        <button
          v-for="(pattern, index) in recent"
          :key="pattern.id"
          class="recent-row"
          @click="openPattern(pattern)"
        >
          <span class="recent-row__index">{{ String(index + 1).padStart(2, '0') }}</span>
          <img :src="pattern.image" :alt="pattern.name" loading="lazy" />
          <span class="recent-row__title">
            <strong>{{ pattern.name }}</strong>
            <small>{{ pattern.originalTitle }}</small>
          </span>
          <span class="recent-row__meta">{{ pattern.dynasty }} · {{ pattern.carrier }}</span>
          <span class="recent-row__source">{{ pattern.source }}</span>
          <AppIcon name="arrow" :size="15" />
        </button>
      </div>
    </section>

    <section class="container reading-section">
      <div class="reading-copy">
        <p class="eyebrow">READING THE PATTERN / 05</p>
        <h2 class="section-title">从一条纹样开始</h2>
        <p>
          先看纹样本身，再看它所在的器物、年代与来源。分类不是终点，
          它只是让你从一条线、一组花瓣或一片云气，找到同一谱系中的其他记录。
        </p>
        <RouterLink to="/patterns" class="text-link">从总目开始阅读 <AppIcon name="arrow" :size="14" /></RouterLink>
      </div>
      <div class="reading-indexes">
        <div>
          <span class="eyebrow">CARRIERS</span>
          <div class="chip-row">
            <button
              v-for="item in carriers.slice(0, 6)"
              :key="item.label"
              class="chip"
              @click="goFilter('carrier', item.label)"
            >
              {{ item.label }} {{ item.count }}
            </button>
          </div>
        </div>
        <div>
          <span class="eyebrow">SOURCES</span>
          <p class="reading-note">大都会艺术博物馆 · 克利夫兰艺术博物馆 · Wikimedia Commons · 数字敦煌</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  overflow: hidden;
}

.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--line);
  background: #142025;
}

.hero::before {
  position: absolute;
  inset: -6%;
  background: url('/hero-background.jpg') center / cover no-repeat;
  content: "";
  opacity: 0.36;
  transform: scale(1.06);
}

.hero::after {
  position: absolute;
  inset: 0;
  background: rgba(10, 20, 24, 0.7);
  content: "";
}

.hero__grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 380px);
  gap: clamp(22px, 2.2vw, 32px);
  align-items: center;
  min-height: 590px;
  padding-top: 54px;
  padding-bottom: 54px;
  color: #f5f4ef;
}

.hero .eyebrow {
  color: var(--accent-soft);
  font-size: 19px;
}

.hero__copy {
  max-width: 860px;
}

.hero h1 {
  max-width: 880px;
  margin: 19px 0 24px;
  font-family: var(--serif);
  font-size: clamp(42px, 4.6vw, 56px);
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.2;
  color: #f7f6f1;
}

.hero h1 em {
  color: var(--accent-soft);
  font-style: normal;
}

.hero__intro {
  max-width: 820px;
  color: rgba(245, 244, 239, 0.9);
  font-size: 20px;
  line-height: 1.95;
}

.hero-search {
  display: flex;
  max-width: 500px;
  align-items: center;
  gap: 11px;
  margin-top: 30px;
  border-bottom: 1px solid rgba(245, 244, 239, 0.72);
  color: #f5f4ef;
}

.hero-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  padding: 12px 0;
  font-size: 19px;
  outline: none;
  color: #f5f4ef;
}

.hero-search input::placeholder {
  color: rgba(245, 244, 239, 0.72);
}

.hero-search__submit {
  border: 0;
  background: transparent;
  color: var(--accent-soft);
  font-size: 19px;
}

.hero__numbers {
  display: flex;
  gap: 30px;
  margin-top: 32px;
}

.hero__numbers div {
  display: grid;
  gap: 2px;
}

.hero__numbers strong {
  font-family: var(--serif);
  font-size: 28px;
  font-weight: 500;
  line-height: 1.2;
  color: #f5f4ef;
}

.hero__numbers div:nth-child(1) strong {
  color: #dbe7e8;
}

.hero__numbers div:nth-child(2) strong {
  color: #c4d6d8;
}

.hero__numbers div:nth-child(3) strong {
  color: var(--accent-soft);
}

.hero__numbers span {
  color: rgba(245, 244, 239, 0.8);
  font-size: 19px;
  letter-spacing: 0.08em;
}

.hero__plate {
  position: relative;
  width: min(100%, 370px);
  justify-self: end;
  cursor: default;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.hero__plate::before {
  display: none;
}

.hero__plate-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  color: rgba(242, 241, 236, 0.82);
  font-family: var(--serif);
  font-size: 18px;
  letter-spacing: 0.16em;
}

.hero__plate-kicker::after {
  flex: 1;
  height: 1px;
  background: rgba(242, 241, 236, 0.26);
  content: "";
}

.hero__stack {
  position: relative;
  width: calc(100% - 24px);
  padding-bottom: 46px;
}

.hero__card {
  position: absolute;
  inset: 0;
  cursor: pointer;
  transition: transform 0.5s var(--ease), opacity 0.5s var(--ease);
}

.hero__card.is-active {
  position: relative;
  z-index: 3;
  transform: none;
}

.hero__card.is-behind-1 {
  z-index: 2;
  transform: translate(12px, 20px) rotate(1.5deg) scale(0.97);
}

.hero__card.is-behind-2 {
  z-index: 1;
  transform: translate(36px, 40px) rotate(-1.5deg) scale(0.93);
}

.hero__card .hero__plate-image {
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
}

.hero__card:not(.is-active) .hero__plate-image {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.hero__card:not(.is-active) .hero__plate-image img {
  filter: saturate(0.55) brightness(0.55);
}

.hero__plate-image {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(245, 244, 239, 0.38);
  border-radius: 2px;
  background: var(--paper-deep);
}

.hero__plate-image img {
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  object-position: center;
  filter: saturate(0.92);
  transform: scale(1.36);
  transition: transform 0.8s var(--ease);
}

.hero__card.is-active:hover .hero__plate-image img {
  transform: scale(1.4);
}

.hero__stack-nav {
  display: flex;
  min-height: 28px;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
}

.hero__nav-arrow {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid rgba(245, 244, 239, 0.4);
  border-radius: 50%;
  background: transparent;
  color: rgba(245, 244, 239, 0.9);
  transition: border-color 0.25s var(--ease), color 0.25s var(--ease);
}

.hero__nav-arrow:hover {
  border-color: rgba(245, 244, 239, 0.8);
  color: var(--paper-soft);
}

.hero__nav-arrow--prev {
  transform: rotate(180deg);
}

.hero__dot {
  position: relative;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  background: transparent;
}

.hero__dot::before {
  position: absolute;
  inset: 7px;
  border: 1px solid rgba(245, 244, 239, 0.5);
  border-radius: 50%;
  content: "";
}

.hero__dot.is-active::before {
  border-color: rgba(245, 244, 239, 0.92);
  background: rgba(245, 244, 239, 0.92);
}

.hero__plate figcaption {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: baseline;
  gap: 8px 16px;
  margin-top: 12px;
  padding: 12px 2px 0;
  border-top: 1px solid rgba(245, 244, 239, 0.34);
  color: rgba(245, 244, 239, 0.92);
  font-size: 18px;
}

.hero__plate figcaption > .catalogue-no {
  grid-column: 1;
  grid-row: 1;
}

.hero__plate .catalogue-no {
  color: rgba(245, 244, 239, 0.74);
}

.hero__caption-name {
  grid-column: 2;
  grid-row: 1;
  justify-self: end;
  max-width: 100%;
  overflow: hidden;
  font-family: var(--serif);
  font-size: 19px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero__caption-tags {
  display: flex;
  grid-column: 1 / -1;
  grid-row: 2;
  gap: 6px;
  justify-self: start;
}

.hero__caption-tags span {
  padding: 1px 7px;
  border: 1px solid rgba(245, 244, 239, 0.5);
  border-radius: 4px;
  color: rgba(245, 244, 239, 0.92);
  font-size: 18px;
}

.hero__swatches {
  display: flex;
  grid-column: 1 / -1;
  grid-row: 3;
  flex-basis: 100%;
  gap: 8px;
  align-items: center;
  margin-top: 2px;
}

.hero__swatches span {
  width: 12px;
  height: 12px;
  border: 1px solid rgba(245, 244, 239, 0.52);
  border-radius: 50%;
}

.hero__rule {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 7px;
  opacity: 0.6;
  background-image: radial-gradient(var(--line) 1px, transparent 1px);
  background-size: 9px 7px;
}

.index-section,
.recent-section,
.reading-section {
  padding-top: 82px;
}

.feature-section {
  margin-top: 64px;
  padding: 32px 34px;
  border-radius: var(--radius);
  background: var(--moss-deep);
  color: var(--paper-soft);
}

.feature-section .section-title {
  color: var(--paper-soft);
}

.feature-section .section-note,
.feature-section .eyebrow {
  color: rgba(242, 241, 236, 0.84);
}

.feature-section .text-link {
  color: var(--accent-soft);
  border-bottom-color: rgba(175, 195, 198, 0.56);
}

.index-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--line);
}

.index-item {
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr) auto;
  grid-template-rows: auto auto;
  column-gap: 12px;
  min-height: 104px;
  padding: 16px 14px;
  border: 0;
  border-right: 1px solid var(--line-soft);
  border-bottom: 1px solid var(--line);
  background: transparent;
  text-align: left;
  transition: background 0.3s var(--ease), padding-left 0.3s var(--ease);
}

.index-item:nth-child(odd) {
  box-shadow: inset 0 3px 0 var(--accent-strong);
}

.index-item:nth-child(even) {
  box-shadow: inset 0 3px 0 var(--accent-mid);
}

.index-item:nth-child(4n) {
  border-right: 0;
}

.index-item:hover {
  padding-left: 21px;
  background: rgba(175, 195, 198, 0.2);
}

.index-item__no,
.index-item__en,
.index-item__count {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.12em;
}

.index-item__thumb {
  position: relative;
  grid-row: 1 / span 2;
  width: 72px;
  height: 72px;
  align-self: center;
  overflow: visible;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.index-item__thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.index-item__title {
  display: flex;
  grid-column: 2;
  align-items: baseline;
  gap: 9px;
  min-width: 0;
}

.index-item__no {
  color: var(--terracotta);
  font-size: 18px;
  letter-spacing: 0.1em;
}

.index-item__name {
  overflow: hidden;
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-item__en {
  grid-column: 2;
}

.index-item__count {
  grid-column: 3;
  grid-row: 1 / span 2;
  align-self: center;
  color: var(--terracotta);
}

.index-footnote {
  margin-top: 12px;
  color: var(--ink-mute);
  font-size: 18px;
}

.feature-carousel {
  display: grid;
  gap: 14px;
}

.feature-rail {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
  scroll-snap-type: x mandatory;
}

.feature-rail::-webkit-scrollbar {
  display: none;
}

.feature-rail :deep(.specimen) {
  flex: 0 0 clamp(260px, 28vw, 335px);
  scroll-snap-align: start;
}

.feature-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: rgba(242, 241, 236, 0.84);
}

.feature-controls > span {
  font-size: 18px;
}

.feature-controls > div {
  display: flex;
  gap: 8px;
}

.feature-controls button {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: 1px solid rgba(242, 241, 236, 0.52);
  border-radius: 50%;
  background: transparent;
  color: var(--paper-soft);
  transition: background 0.3s var(--ease), border-color 0.3s var(--ease);
}

.feature-controls button:hover {
  border-color: var(--accent-soft);
  background: rgba(175, 195, 198, 0.16);
}

.control-prev {
  transform: rotate(180deg);
}

.dynasty-section {
  margin-top: 88px;
  padding: 42px 0 48px;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--paper-deep);
}

.dynasty-section .section-head {
  align-items: end;
  margin-bottom: 18px;
}

.dynasty-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 20px;
}

.dynasty-all {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 0 4px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--accent-strong);
  font-size: 18px;
  transition: border-color 0.3s var(--ease), color 0.3s var(--ease);
}

.dynasty-all:hover {
  border-bottom-color: var(--accent-strong);
  color: var(--ink);
}

.recent-list {
  border-top: 1px solid var(--line);
}

.recent-row {
  display: grid;
  grid-template-columns: 40px 62px minmax(190px, 1fr) 190px 200px 22px;
  gap: 14px;
  align-items: center;
  width: 100%;
  padding: 11px 4px;
  border: 0;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
  text-align: left;
  transition: background 0.3s var(--ease), padding-left 0.3s var(--ease);
}

.recent-row:hover {
  padding-left: 10px;
  background: rgba(175, 195, 198, 0.18);
}

.recent-row__index {
  color: var(--ink-mute);
  font-size: 18px;
}

.recent-row img {
  width: 62px;
  height: 62px;
  border-radius: 8px;
  object-fit: contain;
  background: var(--paper-soft);
}

.recent-row__title {
  display: grid;
  gap: 2px;
}

.recent-row__title strong {
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 600;
}

.recent-row__title small,
.recent-row__meta,
.recent-row__source {
  overflow: hidden;
  color: var(--ink-mute);
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reading-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  padding-bottom: 100px;
}

.reading-copy p:not(.eyebrow) {
  max-width: 520px;
  margin: 22px 0;
  color: var(--ink-soft);
  line-height: 2;
}

.reading-indexes {
  display: grid;
  align-content: start;
  gap: 32px;
  padding-top: 7px;
}

.reading-indexes > div {
  display: grid;
  gap: 13px;
}

.reading-note {
  color: var(--ink-soft);
  font-family: var(--serif);
  font-size: 18px;
  line-height: 1.8;
}

@media (max-width: 1120px) {
  .index-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .index-item:nth-child(4n) {
    border-right: 1px solid var(--line-soft);
  }

  .index-item:nth-child(2n) {
    border-right: 0;
  }
}

@media (max-width: 980px) {
  .hero__grid {
    grid-template-columns: 1fr;
    gap: 44px;
    padding-top: 42px;
  }

  .hero__plate {
    width: min(100%, 430px);
    justify-self: start;
  }

  .feature-rail :deep(.specimen) {
    flex-basis: min(74vw, 360px);
  }

  .reading-section {
    grid-template-columns: 1fr;
    gap: 36px;
  }
}

@media (max-width: 700px) {
  .hero h1 {
    font-size: 43px;
  }

  .hero__stack {
    width: calc(100% - 16px);
    padding-bottom: 34px;
  }

  .hero__card.is-behind-1 {
    transform: translate(12px, 14px) rotate(1.2deg) scale(0.97);
  }

  .hero__card.is-behind-2 {
    transform: translate(32px, 28px) rotate(-1.2deg) scale(0.94);
  }

  .hero__stack-nav {
    justify-content: flex-start;
  }

  .hero__numbers {
    gap: 20px;
  }

  .index-grid {
    grid-template-columns: 1fr 1fr;
  }

  .index-item {
    grid-template-columns: 64px 1fr auto;
    column-gap: 8px;
    padding: 12px;
  }

  .index-item__thumb {
    width: 56px;
    height: 56px;
  }

  .index-item__name {
    font-size: 20px;
  }

  .index-item:nth-child(4n) {
    border-right: 1px solid var(--line-soft);
  }

  .index-item:nth-child(2n) {
    border-right: 0;
  }

  .feature-rail :deep(.specimen) {
    flex-basis: 82vw;
  }

  .recent-row {
    grid-template-columns: 28px 48px minmax(0, 1fr) 16px;
    gap: 10px;
  }

  .recent-row img {
    width: 48px;
    height: 48px;
  }

  .recent-row__meta,
  .recent-row__source {
    display: none;
  }

  .dynasty-section .section-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .dynasty-section .section-title {
    white-space: nowrap;
  }

  .dynasty-actions {
    gap: 12px;
  }
}

@media (max-width: 520px) {
  .index-grid {
    grid-template-columns: 1fr;
  }

  .index-item,
  .index-item:nth-child(2n),
  .index-item:nth-child(4n) {
    border-right: 0;
  }
}
</style>
