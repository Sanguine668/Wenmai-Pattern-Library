<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { patterns, motifIndex } from '../data/patterns'
import { notify } from '../lib/toast'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const modes = [
  { id: 'basic', no: '01', label: '基础纹样', note: '纯色底 / 透明底', description: '把主题、构成和颜色定下来，生成可继续使用的纹样素材。' },
  { id: 'wallpaper', no: '02', label: '壁纸创作', note: '手机 / 桌面 / 平板', description: '围绕一个纹样主题，生成有完整画面的壁纸。' },
  { id: 'product', no: '03', label: '产品应用', note: '丝巾 / 团扇 / 包装', description: '把纹样放回器物与日常用品，预览它的应用方式。' },
]

const styles = ['新中式', '水墨', '青花', '鎏金', '剪纸', '现代几何']
const sizes = [
  { label: '手机竖屏 · 9:16', value: '9:16' },
  { label: '桌面横屏 · 16:9', value: '16:9' },
  { label: '平板 · 4:3', value: '4:3' },
]
const colors = [
  { name: '朱砂', hex: '#9E4B3B' },
  { name: '黛蓝', hex: '#2E4A4A' },
  { name: '浅金', hex: '#C9A85C' },
  { name: '月白', hex: '#E8EDEC' },
  { name: '青绿', hex: '#7E8C6B' },
  { name: '赭石', hex: '#8C6239' },
]

const activeMode = ref('basic')
const motif = ref('花卉纹')
const style = ref('新中式')
const size = ref('9:16')
const selectedColors = ref([colors[0], colors[2]])
const generating = ref(false)
const notice = ref('')
const result = ref(null)

const reference = computed(() => {
  return patterns.find((item) => item.motifType === motif.value) || patterns[0]
})

function toggleColor(color) {
  const exists = selectedColors.value.some((item) => item.hex === color.hex)
  if (exists) {
    selectedColors.value = selectedColors.value.filter((item) => item.hex !== color.hex)
  } else if (selectedColors.value.length < 3) {
    selectedColors.value = [...selectedColors.value, color]
  } else {
    notify('最多选择三种主色', 'info')
  }
}

async function generate() {
  if (!API_BASE) {
    notice.value = '生成接口尚未配置。当前可以先从右侧参考馆藏查看同一纹样类型的真实样本；配置 VITE_API_BASE 后即可连接 /api/generations。'
    notify('当前为前端参数界面，生成接口未连接', 'info')
    return
  }
  generating.value = true
  notice.value = ''
  try {
    const response = await fetch(`${API_BASE}/api/generations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: activeMode.value,
        motif: motif.value,
        style: style.value,
        size: size.value,
        colors: selectedColors.value.map((item) => item.hex),
      }),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    result.value = data
    notify('生成任务已提交', 'success')
  } catch (error) {
    notice.value = `生成请求失败：${error.message}`
    notify('生成接口暂时不可用', 'error')
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="page create-page">
    <div class="container">
      <header class="page-head">
        <div>
          <p class="page-kicker">MAKING / 创作台</p>
          <h1 class="page-title">纹样创作</h1>
        </div>
        <p class="page-subtitle">
          先选一条纹样谱系，再决定构成与颜色。右侧的馆藏参考来自真实记录，生成结果由后续模型服务提供。
        </p>
      </header>

      <div class="mode-tabs">
        <button
          v-for="mode in modes"
          :key="mode.id"
          class="mode-tab"
          :class="{ 'is-active': activeMode === mode.id }"
          @click="activeMode = mode.id"
        >
          <span class="mode-tab__no">{{ mode.no }}</span>
          <span class="mode-tab__label">{{ mode.label }}</span>
          <small>{{ mode.note }}</small>
        </button>
      </div>

      <div class="create-layout">
        <section class="create-form paper-panel">
          <div class="form-heading">
            <p class="eyebrow">PARAMETERS / 参数</p>
            <h2>{{ modes.find((mode) => mode.id === activeMode)?.description }}</h2>
          </div>

          <div class="form-section">
            <span class="field-label">01 / 纹样主题</span>
            <div class="chip-row">
              <button
                v-for="item in motifIndex"
                :key="item.label"
                class="chip"
                :class="{ 'is-active': motif === item.label }"
                @click="motif = item.label"
              >
                {{ item.label }}
              </button>
            </div>
          </div>

          <div class="form-section" v-if="activeMode !== 'basic'">
            <span class="field-label">02 / 风格</span>
            <select v-model="style" class="field-select">
              <option v-for="item in styles" :key="item">{{ item }}</option>
            </select>
          </div>

          <div class="form-section" v-if="activeMode === 'wallpaper'">
            <span class="field-label">03 / 画面尺寸</span>
            <select v-model="size" class="field-select">
              <option v-for="item in sizes" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </div>

          <div class="form-section">
            <span class="field-label">
              {{ activeMode === 'basic' ? '02' : '04' }} / 主色
              <small>最多三种</small>
            </span>
            <div class="color-row">
              <button
                v-for="color in colors"
                :key="color.hex"
                class="color-option"
                :class="{ 'is-active': selectedColors.some((item) => item.hex === color.hex) }"
                :title="`${color.name} ${color.hex}`"
                @click="toggleColor(color)"
              >
                <span :style="{ background: color.hex }"></span>
                {{ color.name }}
              </button>
            </div>
          </div>

          <div class="form-section form-section--bottom">
            <div class="submit-line">
              <button class="btn btn--primary" :disabled="generating" @click="generate">
                <AppIcon name="arrow" :size="16" />
                {{ generating ? '提交中…' : '开始生成' }}
              </button>
              <span class="submit-note">{{ API_BASE ? '接口已配置' : '界面模式' }}</span>
            </div>
            <p v-if="notice" class="form-notice">{{ notice }}</p>
          </div>
        </section>

        <aside class="reference-panel">
          <div class="reference-heading">
            <p class="eyebrow">REFERENCE / 馆藏参照</p>
            <span class="catalogue-no">{{ reference.catalog }}</span>
          </div>
          <div class="reference-image">
            <img :src="reference.image" :alt="reference.name" />
          </div>
          <div class="reference-meta">
            <h2>{{ reference.name }}</h2>
            <p>{{ reference.dynasty }} · {{ reference.carrier }} · {{ reference.motifType }}</p>
            <div class="chip-row">
              <span v-for="color in reference.colors" :key="color.hex" class="chip chip--muted">
                {{ color.name }}
              </span>
            </div>
            <RouterLink :to="`/patterns/${reference.id}`" class="text-link">
              打开这份馆藏 <AppIcon name="arrow" :size="14" />
            </RouterLink>
          </div>
        </aside>
      </div>

      <section v-if="result?.image" class="result-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">OUTPUT / 生成结果</p>
            <h2 class="section-title">这次生成</h2>
          </div>
        </div>
        <img :src="result.image" alt="生成结果" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.create-page {
  padding-top: 44px;
}

.mode-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.mode-tab {
  display: grid;
  grid-template-columns: 32px 1fr;
  grid-template-rows: auto auto;
  gap: 2px 8px;
  padding: 17px 18px;
  border: 0;
  border-right: 1px solid var(--line-soft);
  background: transparent;
  text-align: left;
  transition: background 0.3s var(--ease), padding-left 0.3s var(--ease);
}

.mode-tab:last-child {
  border-right: 0;
}

.mode-tab:hover,
.mode-tab.is-active {
  padding-left: 23px;
  background: rgba(49, 87, 97, 0.12);
  box-shadow: inset 0 4px 0 var(--terracotta);
}

.mode-tab__no {
  grid-row: span 2;
  padding-top: 4px;
  color: var(--ink-mute);
  font-size: 18px;
  letter-spacing: 0.12em;
}

.mode-tab__label {
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 500;
}

.mode-tab small {
  color: var(--ink-mute);
  font-size: 18px;
}

.create-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(300px, 0.72fr);
  gap: 52px;
  align-items: start;
  padding-top: 34px;
}

.create-form {
  padding: 28px 30px 24px;
  border-top: 4px solid var(--moss-deep);
}

.form-heading {
  padding-bottom: 17px;
  border-bottom: 1px solid var(--line);
}

.form-heading h2 {
  max-width: 480px;
  margin-top: 8px;
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 500;
  line-height: 1.6;
}

.form-section {
  padding: 21px 0;
  border-bottom: 1px solid var(--line-soft);
}

.form-section .field-label small {
  margin-left: 9px;
  color: var(--ink-mute);
  font-size: 18px;
}

.form-section .chip-row {
  margin-top: 12px;
}

.color-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 15px;
  margin-top: 12px;
}

.color-option {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: var(--ink-soft);
  font-size: 18px;
}

.color-option span {
  width: 21px;
  height: 21px;
  border: 2px solid transparent;
  border-radius: 50%;
  outline: 1px solid var(--line);
}

.color-option.is-active span {
  border-color: var(--paper-soft);
  outline: 2px solid var(--terracotta);
}

.form-section--bottom {
  border-bottom: 0;
}

.submit-line {
  display: flex;
  align-items: center;
  gap: 14px;
}

.submit-note {
  color: var(--ink-mute);
  font-size: 18px;
}

.form-notice {
  max-width: 600px;
  margin-top: 15px;
  padding-left: 12px;
  border-left: 2px solid var(--ochre);
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.7;
}

.reference-panel {
  position: sticky;
  top: 104px;
  padding-top: 16px;
  border-top: 4px solid var(--terracotta);
}

.reference-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 11px;
  border-bottom: 1px solid var(--line);
}

.reference-image {
  overflow: hidden;
  margin-top: 14px;
  border: 2px solid var(--moss-deep);
  border-radius: var(--radius);
  background: var(--paper-deep);
}

.reference-image img {
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: contain;
  padding: 10px;
  background: var(--paper-soft);
}

.reference-meta {
  padding-top: 15px;
}

.reference-meta h2 {
  font-family: var(--serif);
  font-size: 24px;
  font-weight: 500;
  line-height: 1.45;
}

.reference-meta p {
  margin: 4px 0 13px;
  color: var(--ink-mute);
  font-size: 18px;
}

.reference-meta .text-link {
  margin-top: 17px;
}

.result-section {
  padding-top: 68px;
}

.result-section > img {
  max-width: 620px;
  margin-top: 16px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

@media (max-width: 940px) {
  .create-layout {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .reference-panel {
    position: static;
    max-width: 460px;
  }
}

@media (max-width: 650px) {
  .mode-tabs {
    grid-template-columns: 1fr;
  }

  .mode-tab {
    border-right: 0;
    border-bottom: 1px solid var(--line-soft);
  }

  .mode-tab:last-child {
    border-bottom: 0;
  }

  .create-form {
    padding: 22px 19px;
  }
}
</style>
