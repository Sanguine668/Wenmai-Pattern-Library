<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PatternCard from '../components/PatternCard.vue'
import { useAuth } from '../lib/auth'
import { useLibrary } from '../lib/library'
import { useLibraryStats } from '../lib/stats'
import { notify } from '../lib/toast'

const route = useRoute()
const router = useRouter()
const activeTab = ref('favorites')
const { favoriteItems, historyItems } = useLibrary()
const { currentUser, isAuthenticated, isAdmin, logout } = useAuth()
const { stats } = useLibraryStats()

const favoritePatterns = computed(() => favoriteItems.value)
const historyPatterns = computed(() => historyItems.value)
const denied = computed(() => route.query.denied === 'admin')

const tabs = computed(() => [
  { id: 'favorites', label: '我的收藏', count: favoritePatterns.value.length },
  { id: 'history', label: '浏览记录', count: historyPatterns.value.length },
  { id: 'uploads', label: '上传记录', count: 0 },
  { id: 'creations', label: '创作记录', count: 0 },
])

function openPattern(pattern) {
  router.push(`/patterns/${pattern.id}`)
}

function handleLogout() {
  logout()
  notify('已退出登录')
}
</script>

<template>
  <div class="page profile-page">
    <div class="container">
      <header class="profile-head">
        <div class="profile-seal">纹</div>
        <div class="profile-identity">
          <p class="eyebrow">
            {{ isAuthenticated ? 'READER / 已登录读者' : 'DATABASE READER / 游客浏览' }}
          </p>
          <h1>{{ isAuthenticated ? currentUser.displayName : '未登录的纹样读者' }}</h1>
          <p v-if="isAuthenticated">
            @{{ currentUser.username }}
            <span v-if="isAdmin"> · 管理员</span>
            · 收藏与浏览记录已同步至你的账号。
          </p>
          <p v-else>
            当前使用演示账号；收藏与浏览记录已同步至资源数据库，登录后会记入你自己的账号。
          </p>
        </div>
        <div class="profile-stats">
          <div><strong>{{ favoritePatterns.length }}</strong><span>收藏</span></div>
          <div><strong>{{ historyPatterns.length }}</strong><span>浏览</span></div>
          <div><strong>{{ stats.withImages }}</strong><span>有图档案</span></div>
        </div>
      </header>

      <div class="profile-actions">
        <template v-if="isAuthenticated">
          <RouterLink v-if="isAdmin" to="/admin" class="btn">进入管理后台</RouterLink>
          <button type="button" class="btn" @click="handleLogout">退出登录</button>
          <span class="profile-actions__note">账号：{{ currentUser.username }}</span>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn--primary">登录 / 注册</RouterLink>
          <span class="profile-actions__note">登录后收藏与浏览记录写入你自己的账号</span>
        </template>
      </div>

      <p v-if="denied" class="profile-notice">
        管理后台需要管理员权限，请使用管理员账号登录后再进入。
      </p>

      <div class="tab-line">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-button"
          :class="{ 'is-active': activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
          <small>{{ tab.count }}</small>
        </button>
      </div>

      <section v-if="activeTab === 'favorites'" class="profile-content">
        <div v-if="favoritePatterns.length" class="profile-grid">
          <PatternCard
            v-for="pattern in favoritePatterns"
            :key="pattern.id"
            :pattern="pattern"
            @click="openPattern"
          />
        </div>
        <div v-else class="profile-empty">
          <p class="eyebrow">NO FAVORITES</p>
          <h2>还没有收藏</h2>
          <p>在纹样卡片右上角点一下收藏，这里会留下你的阅读线索。</p>
          <RouterLink to="/patterns" class="btn">去纹样库看看</RouterLink>
        </div>
      </section>

      <section v-if="activeTab === 'history'" class="profile-content">
        <div v-if="historyPatterns.length" class="history-list">
          <button
            v-for="(pattern, index) in historyPatterns"
            :key="pattern.id"
            class="history-row"
            @click="openPattern(pattern)"
          >
            <span class="catalogue-no">{{ String(index + 1).padStart(2, '0') }}</span>
            <img :src="pattern.image" :alt="pattern.name" />
            <span class="history-row__name">{{ pattern.name }}</span>
            <span class="history-row__meta">{{ pattern.dynasty }} · {{ pattern.carrier }}</span>
            <span class="history-row__source">{{ pattern.source }}</span>
          </button>
        </div>
        <div v-else class="profile-empty">
          <p class="eyebrow">NO HISTORY</p>
          <h2>还没有浏览记录</h2>
          <p>打开任意一条纹样档案，这里会记录你最近阅读过的条目。</p>
          <RouterLink to="/patterns" class="btn">浏览纹样总目</RouterLink>
        </div>
      </section>

      <section v-if="activeTab === 'uploads'" class="profile-content">
        <div class="profile-empty">
          <p class="eyebrow">UPLOADS / 后端口</p>
          <h2>上传记录待账号接入</h2>
          <p>识别接口与用户上传记录接通后，这里会显示你的上传图片、预测标签与审核状态。</p>
          <RouterLink to="/upload" class="btn">前往上传识别</RouterLink>
        </div>
      </section>

      <section v-if="activeTab === 'creations'" class="profile-content">
        <div class="profile-empty">
          <p class="eyebrow">CREATIONS / 后端口</p>
          <h2>创作记录待生成服务接入</h2>
          <p>创作任务接通后，这里会保留你的模式、参数、生成图和分类自检结果。</p>
          <RouterLink to="/create" class="btn">打开纹样创作</RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding-top: 44px;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 25px;
  padding-top: 24px;
  padding-bottom: 32px;
  border-top: 4px solid var(--moss-deep);
  border-bottom: 1px solid var(--line);
}

.profile-seal {
  display: grid;
  flex: 0 0 auto;
  width: 74px;
  height: 74px;
  place-items: center;
  border-radius: 16px;
  background: var(--terracotta);
  color: var(--paper-soft);
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1;
}

.profile-identity {
  min-width: 0;
}

.profile-identity h1 {
  margin-top: 5px;
  font-family: var(--serif);
  font-size: clamp(26px, 3vw, 36px);
  font-weight: 500;
}

.profile-identity p:not(.eyebrow) {
  margin-top: 4px;
  color: var(--ink-mute);
  font-size: 18px;
}

.profile-stats {
  display: flex;
  gap: 34px;
  margin-left: auto;
}

.profile-stats div {
  display: grid;
  gap: 2px;
  justify-items: center;
}

.profile-stats strong {
  font-family: var(--serif);
  font-size: 25px;
  font-weight: 500;
}

.profile-stats div:nth-child(1) strong {
  color: var(--terracotta);
}

.profile-stats div:nth-child(2) strong {
  color: var(--accent-strong);
}

.profile-stats div:nth-child(3) strong {
  color: var(--accent-strong);
}

.profile-stats span {
  color: var(--ink-mute);
  font-size: 18px;
}

.profile-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 18px 0 4px;
  border-bottom: 1px solid var(--line);
}

.profile-actions__note {
  color: var(--ink-mute);
  font-size: 18px;
}

.profile-notice {
  margin-top: 16px;
  border-left: 3px solid var(--accent-strong);
  padding: 7px 0 7px 12px;
  color: var(--accent-deep);
  font-size: 18px;
}

.tab-line {
  display: flex;
  gap: 26px;
  border-bottom: 1px solid var(--line);
}

.tab-button {
  position: relative;
  display: flex;
  align-items: baseline;
  gap: 5px;
  padding: 16px 0;
  border: 0;
  background: transparent;
  color: var(--ink-mute);
  font-family: var(--serif);
  font-size: 18px;
}

.tab-button small {
  font-family: var(--sans);
  font-size: 18px;
}

.tab-button::after {
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 2px;
  background: var(--terracotta);
  content: "";
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s var(--ease);
}

.tab-button:hover,
.tab-button.is-active {
  color: var(--ink);
}

.tab-button.is-active::after {
  transform: scaleX(1);
}

.profile-content {
  padding-top: 28px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.history-list {
  border-top: 1px solid var(--line);
}

.history-row {
  display: grid;
  grid-template-columns: 32px 56px minmax(180px, 1fr) 160px 190px;
  gap: 14px;
  align-items: center;
  width: 100%;
  padding: 11px 5px;
  border: 0;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
  text-align: left;
  transition: padding-left 0.3s var(--ease), background 0.3s var(--ease);
}

.history-row:hover {
  padding-left: 11px;
  background: rgba(175, 195, 198, 0.18);
}

.history-row img {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  object-fit: cover;
}

.history-row__name {
  font-family: var(--serif);
  font-size: 18px;
}

.history-row__meta,
.history-row__source {
  overflow: hidden;
  color: var(--ink-mute);
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-empty {
  display: grid;
  justify-items: start;
  gap: 9px;
  padding: 58px 0 70px;
}

.profile-empty h2 {
  font-family: var(--serif);
  font-size: 28px;
  font-weight: 500;
}

.profile-empty p:not(.eyebrow) {
  max-width: 520px;
  color: var(--ink-mute);
  font-size: 18px;
}

.profile-empty .btn {
  margin-top: 9px;
}

@media (max-width: 1000px) {
  .profile-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 750px) {
  .profile-head {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .profile-stats {
    width: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }

  .profile-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .history-row {
    grid-template-columns: 26px 48px minmax(0, 1fr);
  }

  .history-row img {
    width: 48px;
    height: 48px;
  }

  .history-row__meta,
  .history-row__source {
    display: none;
  }
}
</style>
