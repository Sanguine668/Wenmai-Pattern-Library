<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { apiAsset, apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'
import { notify } from '../lib/toast'

const router = useRouter()
const { currentUser, isAdmin, logout } = useAuth()

const menus = [
  { id: 'overview', label: '数据概览' },
  { id: 'patterns', label: '纹样档案' },
  { id: 'users', label: '用户管理' },
  { id: 'quality', label: '数据质量' },
  { id: 'tags', label: '标签分布' },
]
const activeMenu = ref('overview')
const loading = ref(true)
const connected = ref(false)
const stats = ref({
  total: 0,
  withImages: 0,
  trainable: 0,
  discarded: 0,
  noImage: 0,
})
const meta = ref({ motifs: [], dynasties: [], carriers: [], sources: [] })
const tags = ref([])
const patterns = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 24
const keyword = ref('')
const statusFilter = ref('')
const users = ref([])
const editorOpen = ref(false)
const editingId = ref('')
const saving = ref(false)
const userEditorOpen = ref(false)
const editingUserId = ref(null)

const emptyPattern = () => ({
  name: '',
  original_title: '',
  motif_type: '其他',
  secondary: '',
  dynasty: '年代未定',
  date_text: '',
  carrier: '其他',
  description: '',
  source: 'manual',
  source_id: '',
  source_url: '',
  license: '',
  status: 'confirmed',
  annotator: '',
  notes: '',
  image_url: '',
})
const patternForm = reactive(emptyPattern())
const emptyUser = () => ({
  username: '',
  displayName: '',
  email: '',
  password: '',
  isAdmin: false,
  isActive: true,
})
const userForm = reactive(emptyUser())
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const motifTotal = computed(() =>
  meta.value.motifs.reduce((sum, item) => sum + item.count, 0),
)

function resetPatternForm(values = {}) {
  Object.assign(patternForm, emptyPattern(), values)
}

function resetUserForm(values = {}) {
  Object.assign(userForm, emptyUser(), values)
}

async function loadStatsAndMeta() {
  const [statsData, metaData] = await Promise.all([
    apiFetch('/api/stats'),
    apiFetch('/api/meta'),
  ])
  stats.value = statsData
  meta.value = metaData
  connected.value = true
}

async function loadPatterns() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      limit: String(pageSize),
      offset: String((page.value - 1) * pageSize),
      sort: 'latest',
    })
    if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
    if (statusFilter.value) params.set('status', statusFilter.value)
    const data = await apiFetch(`/api/patterns?${params}`)
    patterns.value = data.items.map((item) => ({ ...item, image: apiAsset(item.image) }))
    total.value = data.total
    page.value = Math.min(page.value, Math.max(1, Math.ceil(data.total / pageSize)))
    connected.value = true
  } catch (error) {
    connected.value = false
    notify(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    users.value = await apiFetch('/api/users')
  } catch (error) {
    notify(error.message, 'error')
  }
}

async function loadTags() {
  try {
    tags.value = await apiFetch('/api/tags')
  } catch (error) {
    notify(error.message, 'error')
  }
}

async function refreshAll() {
  await Promise.all([loadStatsAndMeta(), loadPatterns(), loadUsers(), loadTags()])
}

function switchMenu(id) {
  activeMenu.value = id
}

function searchPatterns() {
  page.value = 1
  loadPatterns()
}

function changePage(delta) {
  page.value = Math.min(pageCount.value, Math.max(1, page.value + delta))
  loadPatterns()
}

function openCreatePattern() {
  editingId.value = ''
  resetPatternForm()
  editorOpen.value = true
}

function openEditPattern(item) {
  editingId.value = item.id
  resetPatternForm({
    name: item.name,
    original_title: item.originalTitle,
    motif_type: item.motifType,
    secondary: item.secondary,
    dynasty: item.dynasty,
    date_text: item.dateText,
    carrier: item.carrier,
    description: item.description,
    source: item.sourceCode || 'manual',
    source_id: item.sourceId || '',
    source_url: item.sourceUrl,
    license: item.license,
    status: item.status,
    annotator: item.annotator,
    notes: item.notes,
    image_url: /^https?:\/\//i.test(item.image || '') ? item.image : '',
  })
  editorOpen.value = true
}

async function savePattern() {
  if (!patternForm.name.trim()) {
    notify('请填写纹样名称', 'warning')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await apiFetch(`/api/patterns/${encodeURIComponent(editingId.value)}`, {
        method: 'PATCH',
        body: JSON.stringify(patternForm),
      })
      notify('纹样档案已更新', 'success')
    } else {
      await apiFetch('/api/patterns', {
        method: 'POST',
        body: JSON.stringify(patternForm),
      })
      notify('纹样档案已新增', 'success')
    }
    editorOpen.value = false
    await Promise.all([loadPatterns(), loadStatsAndMeta(), loadTags()])
  } catch (error) {
    notify(error.message, 'error')
  } finally {
    saving.value = false
  }
}

async function deletePattern(item) {
  if (!window.confirm(`确定删除“${item.name}”吗？该操作不可撤销。`)) return
  try {
    await apiFetch(`/api/patterns/${encodeURIComponent(item.id)}`, { method: 'DELETE' })
    notify('纹样档案已删除', 'success')
    await Promise.all([loadPatterns(), loadStatsAndMeta(), loadTags()])
  } catch (error) {
    notify(error.message, 'error')
  }
}

function openCreateUser() {
  editingUserId.value = null
  resetUserForm()
  userEditorOpen.value = true
}

function openEditUser(item) {
  editingUserId.value = item.id
  resetUserForm({
    username: item.username,
    displayName: item.displayName,
    email: item.email,
    isAdmin: item.isAdmin,
    isActive: item.isActive,
  })
  userEditorOpen.value = true
}

async function saveUser() {
  if (!userForm.username.trim() || !userForm.displayName.trim()) {
    notify('请填写用户名和显示名称', 'warning')
    return
  }
  if (!editingUserId.value && !userForm.password) {
    notify('新建用户必须设置初始密码', 'warning')
    return
  }
  saving.value = true
  try {
    if (editingUserId.value) {
      await apiFetch(`/api/users/${editingUserId.value}`, {
        method: 'PATCH',
        body: JSON.stringify({
          display_name: userForm.displayName,
          email: userForm.email,
          password: userForm.password || null,
          is_admin: userForm.isAdmin,
          is_active: userForm.isActive,
        }),
      })
      notify('用户信息已更新', 'success')
    } else {
      await apiFetch('/api/users', {
        method: 'POST',
        body: JSON.stringify({
          username: userForm.username,
          display_name: userForm.displayName,
          email: userForm.email,
          password: userForm.password || null,
          is_admin: userForm.isAdmin,
          is_active: userForm.isActive,
        }),
      })
      notify('用户已创建', 'success')
    }
    userEditorOpen.value = false
    await loadUsers()
  } catch (error) {
    notify(error.message, 'error')
  } finally {
    saving.value = false
  }
}

async function deleteUser(item) {
  if (!window.confirm(`确定删除用户“${item.displayName}”吗？`)) return
  try {
    await apiFetch(`/api/users/${item.id}`, { method: 'DELETE' })
    notify('用户已删除', 'success')
    await loadUsers()
  } catch (error) {
    notify(error.message, 'error')
  }
}

function handleLogout() {
  logout()
  notify('已退出登录')
  router.replace('/login')
}

function handleUnauthorized() {
  notify('登录状态已失效，请重新登录', 'error')
  router.replace({ path: '/login', query: { redirect: '/admin' } })
}

onMounted(() => {
  if (!isAdmin.value) {
    router.replace({ path: '/login', query: { redirect: '/admin' } })
    return
  }
  window.addEventListener('wenmai:unauthorized', handleUnauthorized)
  refreshAll()
})

onBeforeUnmount(() => {
  window.removeEventListener('wenmai:unauthorized', handleUnauthorized)
})
</script>

<template>
  <div class="admin-page">
    <div class="admin-shell">
      <aside class="admin-side">
        <RouterLink to="/" class="admin-brand">
          <span>纹</span>
          <strong>中华纹脉</strong>
        </RouterLink>
        <p class="eyebrow">ADMIN / 数据库编目</p>
        <nav class="admin-nav">
          <button
            v-for="menu in menus"
            :key="menu.id"
            :class="{ 'is-active': activeMenu === menu.id }"
            @click="switchMenu(menu.id)"
          >
            {{ menu.label }}
          </button>
        </nav>
        <div class="admin-foot">
          <span class="eyebrow">SIGNED IN / 管理员</span>
          <p>{{ currentUser ? currentUser.displayName : '管理员' }}<br />{{ currentUser ? currentUser.username : '' }}</p>
          <button type="button" class="admin-logout" @click="handleLogout">退出登录</button>
          <RouterLink to="/patterns" class="text-link">
            返回公开站点 <AppIcon name="arrow" :size="13" />
          </RouterLink>
        </div>
      </aside>

      <main class="admin-main">
        <header class="admin-head">
          <div>
            <p class="page-kicker">CATALOGUE OFFICE / 编目台</p>
            <h1 class="page-title">{{ menus.find((item) => item.id === activeMenu)?.label }}</h1>
          </div>
          <span class="admin-status" :class="{ 'is-offline': !connected }">
            {{ connected ? '数据库已连接' : '数据库未连接' }}
          </span>
        </header>

        <section v-if="activeMenu === 'overview'" class="admin-section">
          <div class="metric-grid">
            <div class="metric"><span>档案总量</span><strong>{{ stats.total }}</strong><small>全部资源记录</small></div>
            <div class="metric"><span>有图记录</span><strong>{{ stats.withImages }}</strong><small>关联本地图片</small></div>
            <div class="metric"><span>已校核</span><strong>{{ stats.trainable }}</strong><small>可进入识别训练</small></div>
            <div class="metric"><span>已舍弃</span><strong>{{ stats.discarded }}</strong><small>保留质量记录</small></div>
            <div class="metric"><span>待补图</span><strong>{{ stats.noImage }}</strong><small>仅保留元数据</small></div>
          </div>

          <div class="overview-grid">
            <section class="paper-panel admin-panel">
              <div class="panel-head">
                <div><p class="eyebrow">MOTIF BALANCE</p><h2>纹样类型分布</h2></div>
                <span>{{ motifTotal }} 条</span>
              </div>
              <div class="bar-list">
                <div v-for="item in meta.motifs" :key="item.label" class="bar-row">
                  <span>{{ item.label }}</span>
                  <div class="bar-track">
                    <i :style="{ width: `${Math.max(3, item.count / Math.max(1, motifTotal) * 100)}%` }"></i>
                  </div>
                  <small>{{ item.count }}</small>
                </div>
              </div>
            </section>

            <section class="paper-panel admin-panel">
              <div class="panel-head">
                <div><p class="eyebrow">DATABASE STATUS</p><h2>数据服务</h2></div>
                <span>{{ connected ? '在线' : '离线' }}</span>
              </div>
              <div class="source-list">
                <div v-for="item in meta.sources" :key="item.value">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
              <p class="panel-note">
                资源、图片、标签、用户、收藏与浏览记录均通过 REST API 读写。
                编目操作完成后，公开纹样库会立即读取最新数据。
              </p>
            </section>
          </div>
        </section>

        <section v-if="activeMenu === 'patterns'" class="admin-section">
          <div class="table-toolbar">
            <label class="table-search">
              <AppIcon name="search" :size="16" />
              <input
                v-model="keyword"
                type="search"
                placeholder="名称、原文标题、编号或描述"
                @keyup.enter="searchPatterns"
              />
            </label>
            <select v-model="statusFilter" class="admin-select" @change="searchPatterns">
              <option value="">全部状态</option>
              <option value="confirmed">已确认</option>
              <option value="discarded">已舍弃</option>
              <option value="no_image">待补图</option>
            </select>
            <button class="btn btn--primary" @click="openCreatePattern">新增纹样</button>
          </div>

          <div class="table-meta">
            <span>共 {{ total }} 条，当前第 {{ page }} / {{ pageCount }} 页</span>
            <button class="text-link" @click="searchPatterns">刷新</button>
          </div>

          <div class="archive-table-wrap">
            <table class="archive-table">
              <thead>
                <tr>
                  <th>编号</th><th>图像</th><th>名称</th><th>类型</th>
                  <th>朝代</th><th>载体</th><th>来源</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loading"><td colspan="8" class="table-empty">正在读取数据库…</td></tr>
                <tr v-for="item in patterns" v-else :key="item.id">
                  <td class="catalogue-no">{{ item.catalog }}</td>
                  <td>
                    <img v-if="item.image" :src="item.image" :alt="item.name" class="table-thumb" />
                    <span v-else class="no-thumb">无图</span>
                  </td>
                  <td class="name-cell">{{ item.name }}</td>
                  <td>{{ item.motifType }}</td>
                  <td>{{ item.dynasty }}</td>
                  <td>{{ item.carrier }}</td>
                  <td>{{ item.source }}</td>
                  <td>
                    <div class="row-actions">
                      <button @click="openEditPattern(item)">编辑</button>
                      <button class="danger" @click="deletePattern(item)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!loading && !patterns.length">
                  <td colspan="8" class="table-empty">没有符合条件的档案</td>
                </tr>
              </tbody>
            </table>
          </div>

          <nav class="admin-pagination">
            <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
            <span>{{ page }} / {{ pageCount }}</span>
            <button :disabled="page >= pageCount" @click="changePage(1)">下一页</button>
          </nav>
        </section>

        <section v-if="activeMenu === 'users'" class="admin-section">
          <div class="table-toolbar">
            <div>
              <strong>{{ users.length }}</strong>
              <span> 个用户</span>
            </div>
            <button class="btn btn--primary" @click="openCreateUser">新增用户</button>
          </div>
          <div class="archive-table-wrap">
            <table class="archive-table">
              <thead>
                <tr><th>ID</th><th>用户名</th><th>显示名称</th><th>邮箱</th><th>角色</th><th>状态</th><th>操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in users" :key="item.id">
                  <td>{{ item.id }}</td>
                  <td>{{ item.username }}</td>
                  <td>{{ item.displayName }}</td>
                  <td>{{ item.email || '未填写' }}</td>
                  <td>{{ item.isAdmin ? '管理员' : '普通用户' }}</td>
                  <td>{{ item.isActive ? '启用' : '停用' }}</td>
                  <td>
                    <div class="row-actions">
                      <button @click="openEditUser(item)">编辑</button>
                      <button
                        class="danger"
                        :disabled="item.username === 'demo' || item.id === currentUser?.id"
                        @click="deleteUser(item)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="activeMenu === 'quality'" class="admin-section quality-grid">
          <article class="paper-panel quality-card">
            <p class="eyebrow">MISSING IMAGES</p>
            <strong>{{ stats.noImage }}</strong>
            <h2>没有本地图片</h2>
            <p>仅保留来源和元数据，补图后可进入浏览与视觉模型训练。</p>
          </article>
          <article class="paper-panel quality-card">
            <p class="eyebrow">DISCARDED</p>
            <strong>{{ stats.discarded }}</strong>
            <h2>已判定舍弃</h2>
            <p>素面器物、无纹饰器件与立体造像保留为质量记录。</p>
          </article>
          <article class="paper-panel quality-card">
            <p class="eyebrow">TRAINABLE</p>
            <strong>{{ stats.trainable }}</strong>
            <h2>可训练记录</h2>
            <p>图片、人工标签与来源信息齐全，可用于后续分类训练。</p>
          </article>
        </section>

        <section v-if="activeMenu === 'tags'" class="admin-section tag-table">
          <div class="panel-head">
            <div><p class="eyebrow">TAG DICTIONARY</p><h2>标签字典</h2></div>
            <span>{{ tags.length }} 个标签</span>
          </div>
          <div v-for="item in tags" :key="`${item.dimension}-${item.name}`" class="tag-row">
            <span class="tag-row__name">{{ item.name }}</span>
            <span class="tag-row__en">{{ item.dimension }}</span>
            <span class="tag-row__count">{{ item.count }} 条</span>
          </div>
        </section>
      </main>
    </div>

    <div v-if="editorOpen" class="editor-overlay" @click.self="editorOpen = false">
      <section class="editor-panel" role="dialog" aria-modal="true">
        <header>
          <div><p class="eyebrow">PATTERN RECORD</p><h2>{{ editingId ? '编辑纹样档案' : '新增纹样档案' }}</h2></div>
          <button class="editor-close" aria-label="关闭" @click="editorOpen = false">
            <AppIcon name="close" :size="20" />
          </button>
        </header>
        <form class="editor-form" @submit.prevent="savePattern">
          <label><span>纹样名称</span><input v-model="patternForm.name" required /></label>
          <label><span>原始标题</span><input v-model="patternForm.original_title" /></label>
          <label>
            <span>纹样类型</span>
            <select v-model="patternForm.motif_type">
              <option v-for="item in meta.motifs" :key="item.label" :value="item.label">{{ item.label }}</option>
              <option value="其他">其他</option>
            </select>
          </label>
          <label>
            <span>朝代</span>
            <select v-model="patternForm.dynasty">
              <option v-for="item in meta.dynasties" :key="item.label" :value="item.label">{{ item.label }}</option>
              <option value="年代未定">年代未定</option>
            </select>
          </label>
          <label>
            <span>文物载体</span>
            <select v-model="patternForm.carrier">
              <option v-for="item in meta.carriers" :key="item.label" :value="item.label">{{ item.label }}</option>
              <option value="其他">其他</option>
            </select>
          </label>
          <label><span>年代描述</span><input v-model="patternForm.date_text" /></label>
          <label><span>来源代码</span><input v-model="patternForm.source" /></label>
          <label><span>来源编号</span><input v-model="patternForm.source_id" :disabled="Boolean(editingId)" /></label>
          <label class="editor-form__wide"><span>来源链接</span><input v-model="patternForm.source_url" type="url" /></label>
          <label class="editor-form__wide"><span>图片直链</span><input v-model="patternForm.image_url" type="url" /></label>
          <label><span>许可信息</span><input v-model="patternForm.license" /></label>
          <label>
            <span>状态</span>
            <select v-model="patternForm.status">
              <option value="confirmed">已确认</option>
              <option value="discarded">已舍弃</option>
              <option value="no_image">待补图</option>
            </select>
          </label>
          <label class="editor-form__wide"><span>说明</span><textarea v-model="patternForm.description" rows="5"></textarea></label>
          <label class="editor-form__wide"><span>编目备注</span><textarea v-model="patternForm.notes" rows="3"></textarea></label>
          <footer class="editor-form__wide">
            <button type="button" class="btn" @click="editorOpen = false">取消</button>
            <button type="submit" class="btn btn--primary" :disabled="saving">
              {{ saving ? '正在保存…' : '保存档案' }}
            </button>
          </footer>
        </form>
      </section>
    </div>

    <div v-if="userEditorOpen" class="editor-overlay" @click.self="userEditorOpen = false">
      <section class="editor-panel editor-panel--small" role="dialog" aria-modal="true">
        <header>
          <div><p class="eyebrow">USER RECORD</p><h2>{{ editingUserId ? '编辑用户' : '新增用户' }}</h2></div>
          <button class="editor-close" aria-label="关闭" @click="userEditorOpen = false">
            <AppIcon name="close" :size="20" />
          </button>
        </header>
        <form class="editor-form" @submit.prevent="saveUser">
          <label><span>用户名</span><input v-model="userForm.username" :disabled="Boolean(editingUserId)" required /></label>
          <label><span>显示名称</span><input v-model="userForm.displayName" required /></label>
          <label class="editor-form__wide"><span>邮箱</span><input v-model="userForm.email" type="email" /></label>
          <label class="editor-form__wide"><span>密码</span><input v-model="userForm.password" type="password" :placeholder="editingUserId ? '留空则保持原密码' : '至少 6 位'" /></label>
          <label class="check-line"><input v-model="userForm.isAdmin" type="checkbox" /><span>管理员</span></label>
          <label class="check-line"><input v-model="userForm.isActive" type="checkbox" /><span>启用账号</span></label>
          <footer class="editor-form__wide">
            <button type="button" class="btn" @click="userEditorOpen = false">取消</button>
            <button type="submit" class="btn btn--primary" :disabled="saving">
              {{ saving ? '正在保存…' : '保存用户' }}
            </button>
          </footer>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.admin-page { min-height: 100vh; background: var(--paper-soft); }
.admin-shell { display: grid; grid-template-columns: 250px minmax(0, 1fr); min-height: 100vh; }
.admin-side {
  display: flex;
  flex-direction: column;
  padding: 30px 23px;
  border-right: 1px solid var(--line);
  background: var(--moss-deep);
  color: var(--paper-soft);
}
.admin-brand { display: flex; align-items: center; gap: 9px; margin-bottom: 44px; }
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
  color: var(--paper-soft);
  font-family: var(--serif);
  font-size: 18px;
  letter-spacing: 0.08em;
}
.admin-side .eyebrow { color: rgba(242, 241, 236, 0.82); }
.admin-nav { display: grid; gap: 3px; margin-top: 14px; }
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
.admin-nav button.is-active { padding-left: 6px; color: var(--accent-soft); }
.admin-foot {
  display: grid;
  gap: 8px;
  margin-top: auto;
  padding-top: 28px;
  border-top: 1px solid rgba(242, 241, 236, 0.3);
}
.admin-foot p { color: rgba(242, 241, 236, 0.82); font-size: 18px; line-height: 1.7; }
.admin-foot .text-link { color: var(--accent-soft); }
.admin-foot .admin-logout {
  justify-self: start;
  border: 0;
  border-bottom: 1px solid rgba(175, 195, 198, 0.58);
  background: transparent;
  padding: 0 0 2px;
  color: var(--accent-soft);
  font-size: 18px;
}
.admin-foot .admin-logout:hover { color: var(--paper-soft); }
.admin-main { min-width: 0; width: 100%; max-width: 1320px; padding: 44px 52px 70px; }
.admin-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 19px;
  border-bottom: 1px solid var(--line);
}
.admin-status { color: var(--accent-strong); font-size: 18px; letter-spacing: 0.08em; }
.admin-status::before { display: inline-block; width: 8px; height: 8px; margin-right: 7px; border-radius: 50%; background: currentColor; content: ""; }
.admin-status.is-offline { color: var(--ink-mute); }
.admin-section { padding-top: 27px; }
.metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border-top: 1px solid var(--line); border-left: 1px solid var(--line); }
.metric {
  display: grid;
  gap: 3px;
  min-height: 132px;
  padding: 16px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  box-shadow: inset 0 4px 0 var(--accent-strong);
}
.metric span, .metric small { color: var(--ink-mute); font-size: 18px; }
.metric strong { font-family: var(--serif); font-size: 30px; font-weight: 500; line-height: 1.2; }
.overview-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px; margin-top: 25px; }
.admin-panel { padding: 21px; }
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 15px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-soft);
}
.panel-head h2 { margin-top: 5px; font-family: var(--serif); font-size: 21px; font-weight: 500; }
.panel-head > span { color: var(--ink-mute); font-size: 18px; }
.bar-list { display: grid; gap: 11px; padding-top: 17px; }
.bar-row { display: grid; grid-template-columns: 100px 1fr 40px; gap: 10px; align-items: center; color: var(--ink-soft); font-size: 18px; }
.bar-row small { color: var(--ink-mute); font-size: 18px; text-align: right; }
.bar-track { height: 5px; overflow: hidden; border-radius: 9px; background: var(--line-soft); }
.bar-track i { display: block; height: 100%; border-radius: inherit; background: var(--accent-strong); }
.source-list { display: grid; gap: 8px; padding-top: 16px; }
.source-list div { display: flex; align-items: baseline; justify-content: space-between; padding-bottom: 8px; border-bottom: 1px solid var(--line-soft); color: var(--ink-soft); font-size: 18px; }
.source-list strong { color: var(--accent-strong); font-family: var(--serif); font-size: 21px; font-weight: 500; }
.panel-note { padding-top: 16px; color: var(--ink-mute); font-size: 18px; line-height: 1.8; }
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.table-search { display: flex; flex: 1; align-items: center; gap: 8px; color: var(--ink-mute); }
.table-search input {
  width: min(430px, 100%);
  border: 0;
  background: transparent;
  padding: 8px 0;
  color: var(--ink);
  font-size: 18px;
  outline: none;
}
.admin-select, .editor-form input, .editor-form select, .editor-form textarea {
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--paper-soft);
  padding: 8px 10px;
  color: var(--ink);
  font-size: 18px;
}
.table-meta, .admin-pagination { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 13px; color: var(--ink-mute); font-size: 18px; }
.archive-table-wrap { overflow-x: auto; }
.archive-table { width: 100%; margin-top: 8px; border-collapse: collapse; text-align: left; font-size: 18px; }
.archive-table th { padding: 10px 8px; border-bottom: 1px solid var(--line); color: var(--ink-mute); font-size: 18px; font-weight: 400; white-space: nowrap; }
.archive-table td { padding: 9px 8px; border-bottom: 1px solid var(--line-soft); color: var(--ink-soft); vertical-align: middle; }
.archive-table tbody tr:hover { background: rgba(175, 195, 198, 0.16); }
.table-thumb { width: 58px; height: 58px; border-radius: 5px; object-fit: cover; background: var(--paper-deep); }
.no-thumb { display: grid; width: 58px; height: 58px; place-items: center; background: var(--paper-deep); color: var(--ink-mute); font-size: 18px; }
.name-cell { min-width: 150px; max-width: 230px; color: var(--ink); }
.row-actions { display: flex; gap: 10px; }
.row-actions button { border: 0; border-bottom: 1px solid currentColor; background: transparent; color: var(--accent-strong); padding: 2px 0; font-size: 18px; }
.row-actions button.danger { color: var(--ink-mute); }
.row-actions button:disabled { cursor: not-allowed; opacity: 0.4; }
.table-empty { padding: 45px 12px !important; color: var(--ink-mute) !important; text-align: center; }
.admin-pagination { justify-content: center; }
.admin-pagination button { border: 1px solid var(--line); border-radius: 7px; background: transparent; padding: 7px 13px; color: var(--ink-soft); font-size: 18px; }
.admin-pagination button:disabled { cursor: not-allowed; opacity: 0.4; }
.quality-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 17px; }
.quality-card { padding: 21px; border-top: 4px solid var(--accent-strong); }
.quality-card strong { display: block; margin: 12px 0 1px; font-family: var(--serif); font-size: 37px; font-weight: 500; }
.quality-card h2 { font-family: var(--serif); font-size: 20px; font-weight: 500; }
.quality-card p:not(.eyebrow) { margin-top: 7px; color: var(--ink-mute); font-size: 18px; line-height: 1.8; }
.tag-table { max-width: 850px; }
.tag-row { display: grid; grid-template-columns: 1fr 1fr 100px; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--line-soft); }
.tag-row__name { font-family: var(--serif); font-size: 18px; }
.tag-row__en, .tag-row__count { color: var(--ink-mute); font-size: 18px; letter-spacing: 0.08em; }
.tag-row__count { text-align: right; }
.editor-overlay { position: fixed; z-index: 180; inset: 0; display: grid; place-items: center; padding: 24px; background: rgba(10, 20, 24, 0.72); }
.editor-panel {
  width: min(920px, 100%);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper);
  box-shadow: 0 30px 70px rgba(10, 20, 24, 0.28);
}
.editor-panel--small { width: min(600px, 100%); }
.editor-panel > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 22px 24px; border-bottom: 1px solid var(--line); }
.editor-panel h2 { margin-top: 4px; font-family: var(--serif); font-size: 26px; font-weight: 500; }
.editor-close { display: grid; width: 38px; height: 38px; place-items: center; border: 1px solid var(--line); border-radius: 50%; background: transparent; }
.editor-form { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 22px 24px 26px; }
.editor-form label { display: grid; align-content: start; gap: 6px; color: var(--ink-soft); font-size: 18px; }
.editor-form input:disabled { color: var(--ink-mute); background: var(--paper-deep); }
.editor-form textarea { resize: vertical; }
.editor-form__wide { grid-column: 1 / -1; }
.editor-form footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 6px; }
.check-line { display: flex !important; align-items: center; gap: 9px !important; }
.check-line input { min-height: auto; width: 18px; height: 18px; }
@media (max-width: 1000px) {
  .admin-shell { grid-template-columns: 1fr; }
  .admin-side { flex-direction: row; flex-wrap: wrap; align-items: center; gap: 14px 28px; border-right: 0; border-bottom: 1px solid var(--line); }
  .admin-brand { margin-bottom: 0; }
  .admin-side > .eyebrow, .admin-foot { display: none; }
  .admin-nav { display: flex; gap: 18px; margin-top: 0; overflow-x: auto; }
  .admin-nav button { border-bottom: 0; padding: 4px 0; }
  .admin-main { padding: 32px 22px 55px; }
  .metric-grid { grid-template-columns: repeat(3, 1fr); }
  .overview-grid, .quality-grid { grid-template-columns: 1fr; }
}
@media (max-width: 700px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .table-toolbar { align-items: stretch; flex-direction: column; }
  .table-search input { width: 100%; }
  .editor-form { grid-template-columns: 1fr; }
  .editor-form__wide { grid-column: 1; }
}
</style>
