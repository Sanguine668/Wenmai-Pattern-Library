import { createRouter, createWebHistory } from 'vue-router'
import { ensureSession, isAdmin, isAuthenticated } from '../lib/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/patterns',
      name: 'patterns',
      component: () => import('../views/PatternsView.vue'),
    },
    {
      path: '/patterns/:id',
      name: 'pattern-detail',
      component: () => import('../views/PatternDetailView.vue'),
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/UploadView.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('../views/CreateView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminConsoleView.vue'),
      meta: { requiresAdmin: true },
    },
  ],
})

router.beforeEach(async (to) => {
  await ensureSession()
  if (to.meta.requiresAdmin && !isAdmin.value) {
    if (isAuthenticated.value) {
      return { path: '/profile', query: { denied: 'admin' } }
    }
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && isAuthenticated.value) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/profile'
    const safe = redirect.startsWith('/') && !redirect.startsWith('//')
    return safe ? redirect : '/profile'
  }
  return true
})

export default router
