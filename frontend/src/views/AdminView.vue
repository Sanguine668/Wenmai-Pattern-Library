<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { patterns, motifIndex, libraryStats } from '../data/patterns'

const router = useRouter()
const activeMenu = ref('overview')
const keyword = ref('')

const menus = [
  { id: 'overview', label: '数据概览' },
  { id: 'patterns', label: '纹样档案' },
  { id: 'quality', label: '数据质量' },
  { id: 'tags', label: '标签分布' },
]

const totalMotifs = computed(() => motifIndex.reduce((sum, item) => sum + item.count, 0))
const filteredPatterns = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return patterns.filter((item) =>
    !q || [item.name, item.originalTitle, item.motifType, item.dynasty, item.carrier, item.source]
      .join(' ')
      .toLowerCase()
      .includes(q),
  )
})

function openPattern(pattern) {
  router.push(`/patterns/${pattern.id}`)
}
</script>

<template>
  <div class="admin-page">
    <div class="admin-shell">
      <aside class="admin-side">
        <RouterLink to="/" class="admin-brand">
          <span>纹</span>
          <strong>中华纹脉</strong>
        </RouterLink>
        <p class="eyebrow">ADMIN / 内部</p>
        <nav class="admin-nav">
          <button
            v-for="menu in menus"
            :key="menu.id"
            :class="{ 'is-active': activeMenu === menu.id }"
            @click="activeMenu = menu.id"
          >
            {{ menu.label }}
          </button>
        </nav>
        <div class="admin-foot">
          <span class="eyebrow">DATA FILE</span>
          <p>来自已标注主数据<br />课程非商业使用</p>
          <RouterLink to="/patterns" class="text-link">返回公开站点 <AppIcon name="arrow" :size="13" /></RouterLink>
        </div>
      </aside>

      <main class="admin-main">
        <header class="admin-head">
          <div>
            <p class="page-kicker">CATALOGUE OFFICE / 编目台</p>
            <h1 class="page-title">{{ menus.find((item) => item.id === activeMenu)?.label }}</h1>
          </div>
          <span class="admin-status">本地数据 · 已载入</span>
        </header>

        <section v-if="activeMenu === 'overview'" class="admin-section">
          <div class="metric-grid">
            <div class="metric">
              <span>档案总量</span>
              <strong>{{ libraryStats.total }}</strong>
              <small>所有来源整理后去重</small>
            </div>
            <div class="metric">
              <span>有图记录</span>
              <strong>{{ libraryStats.withImages }}</strong>
              <small>可用于浏览与识别</small>
            </div>
            <div class="metric">
              <span>已校核</span>
              <strong>{{ libraryStats.trainable }}</strong>
              <small>人工确认的纹样类型</small>
            </div>
            <div class="metric">
              <span>已舍弃</span>
              <strong>{{ libraryStats.discarded }}</strong>
              <small>无纹样或非载体</small>
            </div>
            <div class="metric">
              <span>待补图</span>
              <strong>{{ libraryStats.noImage }}</strong>
              <small>暂不能进入训练</small>
            </div>
          </div>

          <div class="overview-grid">
            <section class="paper-panel admin-panel">
              <div class="panel-head">
                <div>
                  <p class="eyebrow">MOTIF BALANCE</p>
                  <h2>纹样类型分布</h2>
                </div>
                <span>{{ totalMotifs }} 条已分类</span>
              </div>
              <div class="bar-list">
                <div v-for="item in motifIndex" :key="item.label" class="bar-row">
                  <span>{{ item.label }}</span>
                  <div class="bar-track"><i :style="{ width: `${Math.max(4, item.count / totalMotifs * 100)}%` }"></i></div>
                  <small>{{ item.count }}</small>
                </div>
              </div>
            </section>

            <section class="paper-panel admin-panel">
              <div class="panel-head">
                <div>
                  <p class="eyebrow">CURRENT SAMPLE</p>
                  <h2>前端样本</h2>
                </div>
                <span>{{ patterns.length }} 条</span>
              </div>
              <p class="panel-note">
                前端展台按类型各取若干真实记录。完整数据保留在项目主表中；接入后端后可切换为全量查询。
              </p>
              <div class="sample-list">
                <button v-for="pattern in patterns.slice(0, 4)" :key="pattern.id" @click="openPattern(pattern)">
                  <img :src="pattern.image" :alt="pattern.name" />
                  <span>{{ pattern.name }}</span>
                  <small>{{ pattern.motifType }}</small>
                </button>
              </div>
            </section>
          </div>
        </section>

        <section v-if="activeMenu === 'patterns'" class="admin-section">
          <div class="table-toolbar">
            <label class="table-search">
              <AppIcon name="search" :size="16" />
              <input v-model="keyword" type="search" placeholder="筛选名称、类型、朝代、来源" />
            </label>
            <span>{{ filteredPatterns.length }} 条</span>
          </div>
          <div class="archive-table-wrap">
            <table class="archive-table">
              <thead>
                <tr><th>编号</th><th>名称</th><th>类型</th><th>年代</th><th>载体</th><th>来源</th></tr>
              </thead>
              <tbody>
                <tr v-for="pattern in filteredPatterns" :key="pattern.id" @click="openPattern(pattern)">
                  <td class="catalogue-no">{{ pattern.catalog }}</td>
                  <td>{{ pattern.name }}</td>
                  <td>{{ pattern.motifType }}</td>
                  <td>{{ pattern.dynasty }}</td>
                  <td>{{ pattern.carrier }}</td>
                  <td>{{ pattern.source }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="activeMenu === 'quality'" class="admin-section quality-grid">
          <article class="paper-panel quality-card">
            <p class="eyebrow">MISSING IMAGES</p>
            <strong>{{ libraryStats.noImage }}</strong>
            <h2>没有本地图片</h2>
            <p>ArtIC 图片下载受限，部分 Met 记录缺图。补图后才能进入图片浏览与视觉模型训练。</p>
          </article>
          <article class="paper-panel quality-card">
            <p class="eyebrow">DISCARDED</p>
            <strong>{{ libraryStats.discarded }}</strong>
            <h2>已判定舍弃</h2>
            <p>素面器物、无纹饰器件与立体造像已从训练集移出，保留在质量记录中。</p>
          </article>
          <article class="paper-panel quality-card">
            <p class="eyebrow">TRAINABLE</p>
            <strong>{{ libraryStats.trainable }}</strong>
            <h2>可训练记录</h2>
            <p>图片、人工标签与来源信息齐全。当前类别仍不均衡，云纹、缠枝和文字纹偏少。</p>
          </article>
        </section>

        <section v-if="activeMenu === 'tags'" class="admin-section tag-table">
          <div class="panel-head">
            <div><p class="eyebrow">MOTIF TYPE DIMENSION</p><h2>标签字典</h2></div>
            <span>{{ motifIndex.length }} 类</span>
          </div>
          <div v-for="item in motifIndex" :key="item.label" class="tag-row">
            <span class="tag-row__name">{{ item.label }}</span>
            <span class="tag-row__en">{{ item.en }}</span>
            <span class="tag-row__count">{{ item.count }} 条</span>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: var(--paper-soft);
}

.admin-shell {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  min-height: 100vh;
}

.admin-side {
  display: flex;
  flex-direction: column;
  padding: 30px 23px;
  border-right: 1px solid var(--line);
  background: var(--moss-deep);
  color: var(--paper-soft);
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 44px;
}

.admin-brand span {
  display: grid;
  width: 31px;
  height: 31px;
  place-items: center;
  border-radius: 7px;
  background: var(--terracotta);
  color: var(--paper-soft);
  font-family: var(--serif);
  font-size: 20px;
}

.admin-brand strong {
  font-family: var(--serif);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--paper-soft);
}

.admin-side .eyebrow {
  color: rgba(242, 241, 236, 0.8);
}

.admin-nav {
  display: grid;
  gap: 3px;
  margin-top: 14px;
}

.admin-nav button {
  padding: 9px 0;
  border: 0;
  border-bottom: 1px solid transparent;
  background: transparent;
  color: rgba(242, 241, 236, 0.88);
  text-align: left;
  font-family: var(--serif);
  font-size: 18px;
  transition: color 0.3s var(--ease), padding-left 0.3s var(--ease);
}

.admin-nav button:hover,
.admin-nav button.is-active {
  padding-left: 6px;
  color: var(--ochre);
}

.admin-foot {
  display: grid;
  gap: 8px;
  margin-top: auto;
  padding-top: 28px;
  border-top: 1px solid rgba(242, 241, 236, 0.3);
}

.admin-foot p {
  color: rgba(242, 241, 236, 0.82);
  font-size: 18px;
  line-height: 1.7;
}

.admin-foot .text-link {
  color: var(--accent-soft);
  border-bottom-color: rgba(175, 195, 198, 0.56);
}

.admin-main {
  min-width: 0;
  max-width: 1160px;
  padding: 44px 52px 70px;
}

.admin-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 19px;
  border-bottom: 1px solid var(--line);
}

.admin-status {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.admin-section {
  padding-top: 27px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-left: 1px solid var(--line);
}

.metric {
  display: grid;
  gap: 3px;
  min-height: 132px;
  padding: 16px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.metric span,
.metric small {
  color: var(--ink-mute);
  font-size: 18px;
}

.metric strong {
  font-family: var(--serif);
  font-size: 30px;
  font-weight: 500;
  line-height: 1.2;
}

.metric:nth-child(1) {
  box-shadow: inset 0 4px 0 var(--terracotta);
}

.metric:nth-child(2) {
  box-shadow: inset 0 4px 0 var(--ochre);
}

.metric:nth-child(3) {
  box-shadow: inset 0 4px 0 var(--moss);
}

.metric:nth-child(4) {
  box-shadow: inset 0 4px 0 var(--clay);
}

.metric:nth-child(5) {
  box-shadow: inset 0 4px 0 var(--sage);
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 18px;
  margin-top: 25px;
}

.admin-panel {
  padding: 21px;
}

.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 15px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-soft);
}

.panel-head h2 {
  margin-top: 5px;
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 500;
}

.panel-head > span {
  color: var(--ink-mute);
  font-size: 18px;
}

.bar-list {
  display: grid;
  gap: 11px;
  padding-top: 17px;
}

.bar-row {
  display: grid;
  grid-template-columns: 77px 1fr 28px;
  gap: 10px;
  align-items: center;
  color: var(--ink-soft);
  font-size: 18px;
}

.bar-row small {
  color: var(--ink-mute);
  font-size: 18px;
  text-align: right;
}

.bar-track {
  height: 4px;
  overflow: hidden;
  border-radius: 9px;
  background: rgba(183, 165, 138, 0.34);
}

.bar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--moss);
}

.panel-note {
  padding: 16px 0 8px;
  color: var(--ink-mute);
  font-size: 18px;
  line-height: 1.8;
}

.sample-list {
  display: grid;
  gap: 8px;
}

.sample-list button {
  display: grid;
  grid-template-columns: 38px 1fr auto;
  gap: 9px;
  align-items: center;
  padding: 5px 0;
  border: 0;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
  text-align: left;
}

.sample-list img {
  width: 38px;
  height: 38px;
  border-radius: 5px;
  object-fit: contain;
  background: var(--paper-soft);
}

.sample-list span {
  overflow: hidden;
  font-family: var(--serif);
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-list small {
  color: var(--ink-mute);
  font-size: 18px;
}

.table-toolbar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 15px;
  padding-bottom: 13px;
  border-bottom: 1px solid var(--line);
}

.table-search {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-mute);
}

.table-search input {
  width: min(380px, 65vw);
  border: 0;
  background: transparent;
  padding: 7px 0;
  font-size: 18px;
  outline: none;
}

.table-toolbar > span {
  color: var(--ink-mute);
  font-size: 18px;
}

.archive-table-wrap {
  overflow-x: auto;
}

.archive-table {
  width: 100%;
  margin-top: 8px;
  border-collapse: collapse;
  text-align: left;
  font-size: 18px;
}

.archive-table th {
  padding: 10px 9px;
  border-bottom: 1px solid var(--line);
  color: var(--ink-mute);
  font-size: 18px;
  font-weight: 400;
}

.archive-table td {
  padding: 11px 9px;
  border-bottom: 1px solid var(--line-soft);
  color: var(--ink-soft);
}

.archive-table tbody tr {
  cursor: pointer;
}

.archive-table tbody tr:hover {
  background: rgba(175, 195, 198, 0.18);
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 17px;
}

.quality-card {
  padding: 21px;
  border-top: 4px solid var(--terracotta);
}

.quality-card:nth-child(2) {
  border-top-color: var(--ochre);
}

.quality-card:nth-child(3) {
  border-top-color: var(--moss);
}

.quality-card strong {
  display: block;
  margin: 12px 0 1px;
  font-family: var(--serif);
  font-size: 37px;
  font-weight: 500;
}

.quality-card h2 {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 500;
}

.quality-card p:not(.eyebrow) {
  margin-top: 7px;
  color: var(--ink-mute);
  font-size: 18px;
  line-height: 1.8;
}

.tag-table {
  max-width: 790px;
}

.tag-row {
  display: grid;
  grid-template-columns: 1fr 1fr 80px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--line-soft);
}

.tag-row__name {
  font-family: var(--serif);
  font-size: 18px;
}

.tag-row__en {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.12em;
}

.tag-row__count {
  color: var(--ink-mute);
  font-size: 18px;
  text-align: right;
}

@media (max-width: 1000px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-side {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 14px 28px;
    align-items: center;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .admin-brand {
    margin-bottom: 0;
  }

  .admin-side > .eyebrow,
  .admin-foot {
    display: none;
  }

  .admin-nav {
    display: flex;
    gap: 18px;
    margin-top: 0;
  }

  .admin-nav button {
    border-bottom: 0;
    padding: 4px 0;
    font-size: 18px;
  }

  .admin-main {
    padding: 32px 22px 55px;
  }

  .metric-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .overview-grid,
  .quality-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .metric {
    min-height: 110px;
  }

  .admin-nav {
    overflow-x: auto;
  }
}
</style>
