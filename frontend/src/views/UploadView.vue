<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import { patterns } from '../data/patterns'
import { notify } from '../lib/toast'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const fileInput = ref(null)
const isDragOver = ref(false)
const files = ref([])
const recognizing = ref(false)
const interfaceNotice = ref('')

const canRecognize = computed(() => files.value.length > 0 && !recognizing.value)
const demoPattern = computed(() => patterns.find((item) => item.motifType === '花卉纹') || patterns[0])

function addFiles(fileList) {
  for (const file of fileList) {
    if (!file.type.startsWith('image/')) continue
    const reader = new FileReader()
    reader.onload = (event) => {
      files.value.push({
        file,
        preview: event.target.result,
        status: 'pending',
        result: null,
        confirmed: false,
        isDemo: false,
      })
    }
    reader.readAsDataURL(file)
  }
}

function onFileChange(event) {
  addFiles(event.target.files || [])
  event.target.value = ''
}

function onDrop(event) {
  isDragOver.value = false
  addFiles(event.dataTransfer.files || [])
}

function onPaste(event) {
  const items = [...(event.clipboardData?.items || [])]
  const imageFiles = items
    .filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter(Boolean)
  if (imageFiles.length) addFiles(imageFiles)
}

async function recognize() {
  if (!files.value.length) {
    notify('请先放入一张纹样图片', 'warning')
    return
  }
  if (!API_BASE) {
    interfaceNotice.value = '识别接口尚未配置。设置 VITE_API_BASE 后，这里会把图片发送到 /api/uploads/classify。'
    notify('当前为前端界面模式，识别接口未连接', 'info')
    return
  }

  recognizing.value = true
  try {
    for (const item of files.value) {
      const form = new FormData()
      form.append('file', item.file)
      const response = await fetch(`${API_BASE}/api/uploads/classify`, {
        method: 'POST',
        body: form,
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      item.result = data
      item.status = 'done'
    }
    interfaceNotice.value = ''
    notify('识别完成', 'success')
  } catch (error) {
    interfaceNotice.value = `识别请求失败：${error.message}`
    notify('识别接口暂时不可用', 'error')
  } finally {
    recognizing.value = false
  }
}

function showDemoResult(index) {
  const item = files.value[index]
  if (!item) return
  item.status = 'done'
  item.isDemo = true
  item.result = {
    top3: [
      { name: demoPattern.value.motifType, confidence: null },
      { name: demoPattern.value.carrier, confidence: null },
    ],
  }
}

function confirmResult(item) {
  item.confirmed = true
  notify(item.isDemo ? '已记录示例确认操作' : '已确认识别结果', 'success')
}

function removeFile(index) {
  files.value.splice(index, 1)
}
</script>

<template>
  <div class="page upload-page" @paste.prevent="onPaste">
    <div class="container">
      <header class="page-head">
        <div>
          <p class="page-kicker">IMAGE ENTRY / 图像入档</p>
          <h1 class="page-title">上传识别</h1>
        </div>
        <p class="page-subtitle">
          放入一张纹样图片，识别其类型。支持点击选择、拖拽文件，或直接粘贴剪贴板图片。
        </p>
      </header>

      <div class="upload-layout">
        <section class="upload-main">
          <input ref="fileInput" type="file" accept="image/*" multiple hidden @change="onFileChange" />
          <button
            class="dropzone"
            :class="{ 'is-dragging': isDragOver }"
            @click="fileInput?.click()"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="onDrop"
          >
            <span class="dropzone__icon"><AppIcon name="upload" :size="28" /></span>
            <strong>把纹样图片放到这里</strong>
            <span>点击选择文件，或拖拽 / Ctrl+V 粘贴</span>
            <small>JPG、PNG、WEBP；可一次放入多张</small>
          </button>

          <div v-if="files.length" class="file-section">
            <div class="file-section__head">
              <div>
                <p class="eyebrow">QUEUE / 待处理</p>
                <h2>{{ files.length }} 张图片</h2>
              </div>
              <button class="btn btn--primary" :disabled="!canRecognize" @click="recognize">
                {{ recognizing ? '识别中…' : '开始识别' }}
              </button>
            </div>

            <div v-if="interfaceNotice" class="interface-note">
              {{ interfaceNotice }}
            </div>

            <div class="file-grid">
              <article v-for="(item, index) in files" :key="index" class="file-card">
                <div class="file-card__image">
                  <img :src="item.preview" :alt="item.file.name" />
                  <span v-if="item.isDemo" class="demo-badge">示例</span>
                </div>
                <div class="file-card__body">
                  <div class="file-card__title">
                    <strong>{{ item.file.name }}</strong>
                    <button class="remove-btn" @click="removeFile(index)">
                      <AppIcon name="close" :size="14" />
                    </button>
                  </div>
                  <div v-if="item.status === 'pending'" class="file-card__status">
                    待识别
                    <button class="text-link" @click="showDemoResult(index)">查看结果样式</button>
                  </div>
                  <template v-else-if="item.result">
                    <div class="result-label">
                      {{ item.isDemo ? '示例结果（非模型输出）' : '识别结果' }}
                    </div>
                    <div class="chip-row">
                      <span class="chip is-active">
                        {{ item.result.top3[0].name }}
                        <template v-if="item.result.top3[0].confidence">
                          {{ item.result.top3[0].confidence }}%
                        </template>
                      </span>
                      <span v-for="tag in item.result.top3.slice(1)" :key="tag.name" class="chip chip--muted">
                        {{ tag.name }}
                      </span>
                    </div>
                    <div class="result-actions">
                      <button class="text-link" @click="confirmResult(item)">
                        <AppIcon name="check" :size="14" />
                        {{ item.isDemo ? '记录示例操作' : '确认结果' }}
                      </button>
                      <span v-if="item.confirmed" class="confirmed-mark">已确认</span>
                    </div>
                  </template>
                </div>
              </article>
            </div>
          </div>
        </section>

        <aside class="upload-aside">
          <div class="aside-block">
            <p class="eyebrow">HOW IT WORKS</p>
            <h2>一次入档，留下三类信息</h2>
            <ol class="step-list">
              <li><span>01</span><p>图片进入待处理队列，保留原始文件作为识别与入库依据。</p></li>
              <li><span>02</span><p>模型返回纹样类型的候选标签，由你确认或纠正。</p></li>
              <li><span>03</span><p>确认结果可回流至标注数据，继续补充训练样本。</p></li>
            </ol>
          </div>
          <div class="aside-block aside-block--line">
            <p class="eyebrow">INTERFACE STATUS</p>
            <h2>{{ API_BASE ? '识别接口已配置' : '识别接口未连接' }}</h2>
            <p>
              {{ API_BASE
                ? '图片会提交到 /api/uploads/classify，结果按接口返回展示。'
                : '当前可先查看界面与结果样式；配置 VITE_API_BASE 后即可连接真实模型。' }}
            </p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-page {
  padding-top: 44px;
}

.upload-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 56px;
  align-items: start;
}

.dropzone {
  display: grid;
  width: 100%;
  min-height: 330px;
  place-items: center;
  align-content: center;
  gap: 9px;
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  background: rgba(242, 241, 236, 0.52);
  color: var(--ink-soft);
  text-align: center;
  transition: border-color 0.3s var(--ease), background 0.3s var(--ease);
}

.dropzone:hover,
.dropzone.is-dragging {
  border-color: var(--terracotta);
  background: rgba(49, 87, 97, 0.12);
}

.dropzone__icon {
  display: grid;
  width: 58px;
  height: 58px;
  margin-bottom: 7px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 50%;
  color: var(--terracotta);
}

.dropzone strong {
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 500;
}

.dropzone span:not(.dropzone__icon) {
  font-size: 18px;
}

.dropzone small {
  color: var(--ink-mute);
  font-size: 18px;
}

.file-section {
  margin-top: 38px;
}

.file-section__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 13px;
  border-bottom: 1px solid var(--line);
}

.file-section__head h2 {
  margin-top: 5px;
  font-family: var(--serif);
  font-size: 23px;
  font-weight: 500;
}

.interface-note {
  margin-top: 14px;
  padding: 10px 13px;
  border-left: 2px solid var(--ochre);
  background: rgba(106, 139, 147, 0.14);
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.7;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding-top: 17px;
}

.file-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: rgba(242, 241, 236, 0.56);
}

.file-card__image {
  position: relative;
}

.file-card__image img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.demo-badge {
  position: absolute;
  top: 9px;
  left: 9px;
  padding: 3px 6px;
  border-radius: 3px;
  background: var(--ochre);
  color: var(--paper-soft);
  font-size: 18px;
}

.file-card__body {
  padding: 12px;
}

.file-card__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.file-card__title strong {
  overflow: hidden;
  font-size: 18px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  display: grid;
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  place-items: center;
  border: 0;
  background: transparent;
  color: var(--ink-mute);
}

.file-card__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 8px;
  color: var(--ink-mute);
  font-size: 18px;
}

.result-label {
  margin: 9px 0 7px;
  color: var(--ink-mute);
  font-size: 18px;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  font-size: 18px;
}

.confirmed-mark {
  color: var(--accent-strong);
}

.upload-aside {
  display: grid;
  gap: 30px;
}

.aside-block {
  padding-top: 17px;
  padding-bottom: 23px;
  border-top: 4px solid var(--moss);
  border-bottom: 1px solid var(--line);
}

.aside-block + .aside-block {
  border-top-color: var(--terracotta);
}

.aside-block h2 {
  margin: 7px 0 13px;
  font-family: var(--serif);
  font-size: 20px;
  font-weight: 500;
  line-height: 1.5;
}

.aside-block p {
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.85;
}

.step-list {
  display: grid;
  gap: 14px;
  list-style: none;
}

.step-list li {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 7px;
}

.step-list span {
  color: var(--terracotta);
  font-size: 18px;
  letter-spacing: 0.08em;
}

.step-list p {
  font-size: 18px;
  line-height: 1.75;
}

@media (max-width: 900px) {
  .upload-layout {
    grid-template-columns: 1fr;
    gap: 38px;
  }

  .upload-aside {
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
}

@media (max-width: 580px) {
  .file-grid,
  .upload-aside {
    grid-template-columns: 1fr;
  }
}
</style>
