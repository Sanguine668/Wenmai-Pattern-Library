<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { patterns } from '../data/patterns'
import { useAuth } from '../lib/auth'
import { useMeta } from '../lib/meta'
import { useLibraryStats } from '../lib/stats'
import { notify } from '../lib/toast'

const route = useRoute()
const router = useRouter()
const { login, register, pending } = useAuth()
const { stats, loadLibraryStats } = useLibraryStats()
const { motifs, loadMeta } = useMeta()

const mode = ref('login')
const errorMessage = ref('')
const form = reactive({
  username: '',
  displayName: '',
  email: '',
  password: '',
  confirm: '',
})

const platePatterns = computed(() => {
  const seen = new Set()
  const picks = []
  for (const item of patterns) {
    if (!item.image || seen.has(item.motifType)) continue
    seen.add(item.motifType)
    picks.push(item)
    if (picks.length === 6) break
  }
  return picks
})

const isRegister = computed(() => mode.value === 'register')
const redirectTarget = computed(() => {
  const redirect = route.query.redirect
  if (
    typeof redirect === 'string' &&
    redirect.startsWith('/') &&
    !redirect.startsWith('//')
  ) {
    return redirect
  }
  return '/profile'
})

function switchMode(next) {
  mode.value = next
  errorMessage.value = ''
}

async function submit() {
  errorMessage.value = ''
  const username = form.username.trim()
  if (!username || !form.password) {
    errorMessage.value = '请填写用户名和密码'
    return
  }
  if (isRegister.value) {
    if (!form.displayName.trim()) {
      errorMessage.value = '请填写显示名称'
      return
    }
    if (form.password.length < 6) {
      errorMessage.value = '密码至少需要 6 位'
      return
    }
    if (form.password !== form.confirm) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }
  }
  try {
    if (isRegister.value) {
      await register({
        username,
        displayName: form.displayName.trim(),
        password: form.password,
        email: form.email.trim(),
      })
      notify('注册成功，已自动登录')
    } else {
      await login(username, form.password)
      notify('登录成功')
    }
    router.replace(redirectTarget.value)
  } catch (error) {
    errorMessage.value = error.message || '操作失败，请稍后再试'
  }
}

onMounted(() => {
  loadLibraryStats()
  loadMeta()
})
</script>

<template>
  <div class="page login-page">
    <div class="container login-shell">
      <section class="login-intro">
        <p class="eyebrow">READER ACCOUNT / 读者账号</p>
        <h1>为纹样档案<br />建一枚自己的藏书印。</h1>
        <p class="login-intro__text">
          登录后，收藏与浏览记录会写入你自己的账号，与资源库中的纹样档案一起保存。未登录时仍可以浏览，收藏会记在演示账号名下。
        </p>
        <ul class="login-points">
          <li><span>一</span>收藏的纹样会在个人中心单独归档</li>
          <li><span>二</span>浏览记录自动去重，只保留最近一次阅读</li>
          <li><span>三</span>管理员账号可进入后台编目与用户管理</li>
        </ul>

        <div class="login-ledger">
          <div><strong>{{ stats.total }}</strong><span>条档案记录</span></div>
          <div><strong>{{ stats.withImages }}</strong><span>条有图档案</span></div>
          <div><strong>{{ motifs.length }}</strong><span>类纹样类型</span></div>
        </div>
      </section>

      <section class="login-panel paper-panel">
        <div class="login-tabs" role="tablist" aria-label="账号操作">
          <button
            type="button"
            role="tab"
            :aria-selected="!isRegister"
            class="login-tab"
            :class="{ 'is-active': !isRegister }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="isRegister"
            class="login-tab"
            :class="{ 'is-active': isRegister }"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>

        <form class="login-form" @submit.prevent="submit">
          <label class="field">
            <span class="field-label">用户名</span>
            <input
              v-model="form.username"
              class="field-input"
              type="text"
              autocomplete="username"
              placeholder="例如 reader"
            />
          </label>

          <label v-if="isRegister" class="field">
            <span class="field-label">显示名称</span>
            <input
              v-model="form.displayName"
              class="field-input"
              type="text"
              autocomplete="nickname"
              placeholder="展示在个人中心的称呼"
            />
          </label>

          <label v-if="isRegister" class="field">
            <span class="field-label">邮箱（选填）</span>
            <input
              v-model="form.email"
              class="field-input"
              type="email"
              autocomplete="email"
              placeholder="用于后续找回账号"
            />
          </label>

          <label class="field">
            <span class="field-label">密码</span>
            <input
              v-model="form.password"
              class="field-input"
              type="password"
              :autocomplete="isRegister ? 'new-password' : 'current-password'"
              placeholder="至少 6 位"
            />
          </label>

          <label v-if="isRegister" class="field">
            <span class="field-label">确认密码</span>
            <input
              v-model="form.confirm"
              class="field-input"
              type="password"
              autocomplete="new-password"
              placeholder="再输入一次"
            />
          </label>

          <p v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</p>

          <button type="submit" class="btn btn--primary login-submit" :disabled="pending">
            {{ pending ? '处理中…' : isRegister ? '注册并登录' : '登录' }}
          </button>
        </form>

        <div class="login-foot">
          <p v-if="!isRegister">
            还没有账号？<button type="button" class="text-button" @click="switchMode('register')">
              创建一个读者账号
            </button>
          </p>
          <p v-else>
            已有账号？<button type="button" class="text-button" @click="switchMode('login')">
              直接登录
            </button>
          </p>
        </div>
      </section>
    </div>

    <section class="container login-plates">
      <div class="section-head">
        <div>
          <p class="eyebrow">PLATES / 馆藏图版</p>
          <h2 class="section-title">先从这些档案读起</h2>
        </div>
        <RouterLink to="/patterns" class="text-link">
          浏览全部 {{ stats.total }} 条 <AppIcon name="arrow" :size="14" />
        </RouterLink>
      </div>
      <div class="login-plate-grid">
        <RouterLink
          v-for="item in platePatterns"
          :key="item.id"
          :to="`/patterns/${item.id}`"
          class="login-plate"
        >
          <img :src="item.image" :alt="item.name" loading="lazy" />
          <span class="login-plate__no">{{ item.catalog }}</span>
          <strong>{{ item.name }}</strong>
          <small>{{ item.dynasty }} · {{ item.carrier }}</small>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  padding-top: 48px;
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 480px);
  gap: 56px;
  align-items: start;
}

.login-intro h1 {
  margin: 12px 0 18px;
  font-family: var(--serif);
  font-size: clamp(30px, 3.4vw, 42px);
  font-weight: 600;
  line-height: 1.3;
}

.login-intro__text {
  max-width: 520px;
  color: var(--ink-soft);
  line-height: 1.95;
}

.login-points {
  display: grid;
  gap: 12px;
  margin-top: 28px;
  list-style: none;
}

.login-points li {
  display: flex;
  gap: 12px;
  align-items: baseline;
  color: var(--ink-soft);
}

.login-points span {
  display: inline-grid;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 50%;
  color: var(--accent-strong);
  font-family: var(--serif);
  font-size: 18px;
}

.login-panel {
  padding: 30px 32px 26px;
}

.login-tabs {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid var(--line);
}

.login-tab {
  position: relative;
  padding: 4px 0 13px;
  border: 0;
  background: transparent;
  color: var(--ink-mute);
  font-family: var(--serif);
  font-size: 21px;
  transition: color 0.3s var(--ease);
}

.login-tab::after {
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

.login-tab.is-active {
  color: var(--ink);
}

.login-tab.is-active::after {
  transform: scaleX(1);
}

.login-form {
  display: grid;
  gap: 19px;
  padding-top: 24px;
}

.login-error {
  border-left: 3px solid var(--accent-strong);
  padding: 7px 0 7px 12px;
  color: var(--accent-deep);
  font-size: 18px;
}

.login-submit {
  width: 100%;
  margin-top: 4px;
}

.login-foot {
  display: grid;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
  color: var(--ink-mute);
  font-size: 18px;
}

.text-button {
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  padding: 0;
  color: var(--accent-strong);
  font-size: 18px;
}

.text-button:hover {
  border-bottom-color: var(--terracotta);
  color: var(--terracotta);
}

.login-ledger {
  display: flex;
  flex-wrap: wrap;
  gap: 38px;
  margin-top: 30px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}

.login-ledger div {
  display: grid;
  gap: 2px;
}

.login-ledger strong {
  color: var(--accent-strong);
  font-family: var(--serif);
  font-size: 28px;
  font-weight: 500;
  line-height: 1.2;
}

.login-ledger span {
  color: var(--ink-mute);
  font-size: 18px;
}

.login-plates {
  margin-top: 62px;
  padding-top: 34px;
  border-top: 4px solid var(--moss-deep);
}

.login-plate-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 18px;
}

.login-plate {
  display: grid;
  gap: 6px;
  align-content: start;
}

.login-plate img {
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  border: 1px solid var(--line);
  background: var(--paper-soft);
  transition: border-color 0.3s var(--ease), transform 0.45s var(--ease);
}

.login-plate:hover img {
  border-color: var(--terracotta);
  transform: translateY(-3px);
}

.login-plate__no {
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.05em;
}

.login-plate strong {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 600;
  line-height: 1.4;
}

.login-plate small {
  color: var(--ink-mute);
  font-size: 18px;
  line-height: 1.5;
}

@media (max-width: 1100px) {
  .login-plate-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .login-shell {
    grid-template-columns: minmax(0, 1fr);
    gap: 30px;
  }

  .login-intro__text {
    max-width: none;
  }
}

@media (max-width: 700px) {
  .login-plate-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
}

@media (max-width: 560px) {
  .login-panel {
    padding: 22px 20px 20px;
  }
}
</style>
