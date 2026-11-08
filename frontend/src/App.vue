<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from './components/AppIcon.vue'
import DigitalHuman from './components/DigitalHuman.vue'
import ToastHost from './components/ToastHost.vue'
import { useAuth } from './lib/auth'
import { useLibrary } from './lib/library'
import { useLibraryStats } from './lib/stats'
import { notify } from './lib/toast'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')
const menuOpen = ref(false)
const { favoritesCount, hydrateUserLibrary } = useLibrary()
const { currentUser, isAuthenticated, isAdmin, logout } = useAuth()
const { stats, loadLibraryStats } = useLibraryStats()

const primaryNav = [
  { path: '/', label: '首页' },
  { path: '/patterns', label: '纹样库' },
  { path: '/upload', label: '上传识别' },
  { path: '/create', label: '纹样创作' },
]
const menuNav = [...primaryNav, { path: '/profile', label: '个人中心' }]

function isNavActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

function submitSearch() {
  const keyword = searchQuery.value.trim()
  if (!keyword) return
  router.push({ path: '/patterns', query: { keyword } })
  searchQuery.value = ''
  menuOpen.value = false
}

function handleLogout() {
  logout()
  menuOpen.value = false
  notify('已退出登录')
  if (router.currentRoute.value.meta.requiresAdmin) router.push('/')
}

onMounted(() => {
  hydrateUserLibrary()
  loadLibraryStats()
})
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-inner">
        <RouterLink to="/" class="brand" @click="menuOpen = false">
          <img class="brand__icon" src="/brand-icon.png" alt="" />
          <span class="brand__text">
            <strong>中华纹脉</strong>
            <small>中国图案数字档案</small>
          </span>
        </RouterLink>

        <nav class="desktop-nav" aria-label="主导航">
          <RouterLink
            v-for="link in primaryNav"
            :key="link.path"
            :to="link.path"
            class="nav-link"
            :class="{ 'is-active': isNavActive(link.path) }"
          >
            {{ link.label }}
          </RouterLink>
        </nav>

        <div class="header-tools">
          <form class="search" @submit.prevent="submitSearch">
            <AppIcon name="search" :size="17" />
            <input
              v-model="searchQuery"
              type="search"
              aria-label="检索纹样"
              placeholder="检索纹样、朝代或载体"
            />
          </form>
          <RouterLink to="/profile" class="saved-link" aria-label="查看收藏">
            <AppIcon name="heart" :size="17" />
            <span>{{ favoritesCount }}</span>
          </RouterLink>
          <RouterLink
            to="/profile"
            class="nav-link nav-link--profile"
            :class="{ 'is-active': isNavActive('/profile') }"
          >
            个人中心
          </RouterLink>
          <div class="account">
            <template v-if="isAuthenticated">
              <RouterLink v-if="isAdmin" to="/admin" class="account-link">后台</RouterLink>
              <RouterLink to="/profile" class="account-name">
                {{ currentUser.displayName }}
              </RouterLink>
              <button type="button" class="account-link" @click="handleLogout">退出</button>
            </template>
            <RouterLink v-else to="/login" class="account-link">登录 / 注册</RouterLink>
          </div>
          <button class="menu-trigger" aria-label="打开导航" @click="menuOpen = !menuOpen">
            <AppIcon :name="menuOpen ? 'close' : 'menu'" :size="20" />
          </button>
        </div>
      </div>

      <div v-if="menuOpen" class="mobile-nav">
        <RouterLink
          v-for="link in menuNav"
          :key="link.path"
          :to="link.path"
          class="mobile-nav__link"
          @click="menuOpen = false"
        >
          {{ link.label }}
        </RouterLink>
        <template v-if="isAuthenticated">
          <RouterLink
            v-if="isAdmin"
            to="/admin"
            class="mobile-nav__link"
            @click="menuOpen = false"
          >
            管理后台
          </RouterLink>
          <button type="button" class="mobile-nav__link" @click="handleLogout">
            退出登录（{{ currentUser.displayName }}）
          </button>
        </template>
        <RouterLink
          v-else
          to="/login"
          class="mobile-nav__link"
          @click="menuOpen = false"
        >
          登录 / 注册
        </RouterLink>
      </div>
    </header>

    <main class="site-main">
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="container footer-inner">
        <div>
          <span class="footer-brand">中华纹脉</span>
          <p>中华传统纹样资源档案 · 课程研究项目</p>
        </div>
        <div class="footer-meta">
          <span>{{ stats.total }} 条记录</span>
          <span>{{ stats.withImages }} 条有图</span>
          <span>开放馆藏与授权素材</span>
        </div>
        <RouterLink to="/patterns" class="text-link">
          进入纹样总目 <AppIcon name="arrow" :size="14" />
        </RouterLink>
      </div>
    </footer>

    <DigitalHuman v-if="route.path !== '/login'" />
    <ToastHost />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 80;
  border-bottom: 1px solid var(--line);
  background: rgba(232, 231, 225, 0.97);
}

.site-header::before {
  display: block;
  height: 4px;
  background: var(--accent-strong);
  content: "";
}

.header-inner {
  display: flex;
  width: 100%;
  height: 92px;
  align-items: center;
  gap: clamp(24px, 2.8vw, 52px);
  padding: 0 clamp(20px, 3.4vw, 60px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 0 0 auto;
}

.brand__icon {
  width: 56px;
  height: 56px;
  flex: 0 0 auto;
  object-fit: contain;
}

.brand__text {
  display: grid;
  gap: 1px;
}

.brand__text strong {
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 600;
  letter-spacing: 0.08em;
  line-height: 1.2;
}

.brand__text small {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.04em;
}

.desktop-nav {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-link {
  position: relative;
  display: inline-flex;
  height: 46px;
  align-items: center;
  padding: 0 24px;
  border-bottom: 3px solid transparent;
  border-radius: 5px 5px 0 0;
  color: var(--ink-soft);
  font-size: 18px;
  transition: background 0.28s var(--ease), color 0.28s var(--ease),
    border-color 0.28s var(--ease);
}

.nav-link:hover {
  background: rgba(175, 195, 198, 0.24);
  color: var(--ink);
}

.nav-link.is-active {
  border-bottom-color: var(--accent-strong);
  background: var(--accent-pale);
  color: var(--accent-deep);
  font-weight: 600;
}

.header-tools {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.nav-link--profile {
  padding: 0 16px;
}

.search {
  display: flex;
  width: min(280px, 21vw);
  align-items: center;
  gap: 9px;
  border-bottom: 1px solid var(--line);
  color: var(--ink-mute);
}

.search input {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 8px 0;
  color: var(--ink);
  font-size: 18px;
  outline: none;
}

.search input::placeholder {
  color: var(--ink-mute);
}

.search:focus-within {
  border-bottom-color: var(--moss);
}

.saved-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--ink-soft);
  font-size: 18px;
}

.saved-link:hover {
  color: var(--terracotta);
}

.account {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 16px;
  border-left: 1px solid var(--line-soft);
  color: var(--ink-soft);
  font-size: 18px;
  white-space: nowrap;
}

.account-link {
  border: 0;
  background: transparent;
  padding: 0;
  color: var(--ink-soft);
  font-size: 18px;
  transition: color 0.3s var(--ease);
}

.account-link:hover {
  color: var(--terracotta);
}

.account-name {
  max-width: 120px;
  overflow: hidden;
  color: var(--accent-strong);
  font-family: var(--serif);
  text-overflow: ellipsis;
}

.account-name:hover {
  color: var(--terracotta);
}

.menu-trigger {
  display: none;
  border: 0;
  background: transparent;
  color: var(--ink);
}

.site-main {
  flex: 1;
}

.site-footer {
  border-top: 1px solid var(--line);
  background: var(--moss-deep);
  color: var(--paper-soft);
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding-top: 28px;
  padding-bottom: 28px;
}

.footer-brand {
  font-family: var(--serif);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.footer-inner p,
.footer-meta {
  color: rgba(242, 241, 236, 0.82);
  font-size: 18px;
}

.footer-inner .text-link {
  color: var(--accent-soft);
  border-bottom-color: rgba(175, 195, 198, 0.58);
}

.footer-meta {
  display: flex;
  gap: 18px;
}

.mobile-nav {
  display: none;
}

@media (max-width: 1240px) {
  .search {
    display: none;
  }
}

@media (max-width: 1080px) {
  .header-inner {
    gap: 18px;
  }

  .nav-link {
    padding: 0 12px;
  }

  .nav-link--profile {
    padding: 0 10px;
  }

  .account {
    padding-left: 10px;
    gap: 8px;
  }
}

@media (max-width: 900px) {
  .header-inner {
    height: 82px;
    padding: 0 24px;
    gap: 14px;
  }

  .desktop-nav,
  .nav-link--profile {
    display: none;
  }

  .menu-trigger {
    display: inline-flex;
  }
}

@media (max-width: 720px) {
  .header-inner {
    height: 76px;
    padding: 0 18px;
  }

  .brand {
    gap: 10px;
  }

  .brand__icon {
    width: 44px;
    height: 44px;
  }

  .brand__text strong {
    font-size: 20px;
  }

  .brand__text small {
    display: none;
  }

  .account {
    display: none;
  }

  .mobile-nav {
    display: grid;
    border-top: 1px solid var(--line);
    padding: 8px 18px 18px;
  }

  .mobile-nav__link {
    width: 100%;
    border: 0;
    border-bottom: 1px solid var(--line-soft);
    background: transparent;
    padding: 11px 4px;
    color: var(--ink-soft);
    font-size: 18px;
    text-align: left;
  }

  .footer-inner {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
