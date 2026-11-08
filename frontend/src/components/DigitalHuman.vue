<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import { patterns } from '../data/patterns'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE || ''
const open = ref(false)
const input = ref('')
const thinking = ref(false)
const body = ref(null)
const messages = ref([
  {
    role: 'bot',
    text: '我是纹脉助手，当前先以本地档案做检索。可以问纹样名称、朝代、载体或类别。',
    links: [],
  },
])

const quickQuestions = ['有哪些云纹？', '找清代的瓷器纹样', '人物纹有哪些？']
const status = computed(() => (API_BASE ? '知识库已连接' : '本地档案检索'))

async function scrollToBottom() {
  await nextTick()
  if (body.value) body.value.scrollTop = body.value.scrollHeight
}

function localSearch(question) {
  const tokens = [...new Set(patterns.flatMap((item) => [
    item.motifType,
    item.dynasty,
    item.carrier,
    item.name,
  ]))].filter(Boolean)
  const knownTerms = tokens.filter((token) => question.includes(token))
  const terms = knownTerms.length
    ? knownTerms
    : question
    .replace(/[？?，,。.\s]/g, ' ')
    .split(' ')
    .filter((term) => term.length > 1)
  const matches = patterns.filter((item) => {
    const text = [
      item.name,
      item.originalTitle,
      item.motifType,
      item.secondary,
      item.dynasty,
      item.carrier,
      item.description,
    ].join(' ')
    return terms.some((term) => text.includes(term))
  })
  return matches.slice(0, 4)
}

async function ask(question) {
  if (!question.trim() || thinking.value) return
  messages.value.push({ role: 'user', text: question.trim(), links: [] })
  input.value = ''
  thinking.value = true
  scrollToBottom()

  if (API_BASE) {
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!response.ok) throw new Error('request failed')
      const data = await response.json()
      messages.value.push({
        role: 'bot',
        text: data.answer || '接口没有返回答案。',
        links: (data.citations || []).slice(0, 4).map((item) => ({
          label: item.title || item.source_title || '查看引用',
          id: item.pattern_id,
        })),
      })
    } catch {
      const local = localSearch(question)
      messages.value.push({
        role: 'bot',
        text: local.length
          ? `知识库接口暂时不可用，先在本地档案中找到 ${local.length} 条相关记录。`
          : '知识库接口暂时不可用，本地样本中也没有找到对应记录。',
        links: local.map((item) => ({ label: item.name, id: item.id })),
      })
    }
  } else {
    await new Promise((resolve) => setTimeout(resolve, 420))
    const local = localSearch(question)
    messages.value.push({
      role: 'bot',
      text: local.length
        ? `在本地档案中找到 ${local.length} 条相关记录。完整知识库问答待后端接入后启用。`
        : '本地样本中没有找到对应记录。可以换一个纹样类别、朝代或载体再试。',
      links: local.map((item) => ({ label: item.name, id: item.id })),
    })
  }

  thinking.value = false
  scrollToBottom()
}

function useQuick(question) {
  ask(question)
}

function openLink(link) {
  if (link.id) {
    router.push(`/patterns/${link.id}`)
    open.value = false
  }
}
</script>

<template>
  <div class="assistant">
    <transition name="panel">
      <section v-if="open" class="assistant-panel" aria-label="纹脉助手">
        <header class="assistant-head">
          <div>
            <span class="eyebrow">ASSISTANT / 纹脉助手</span>
            <strong>{{ status }}</strong>
          </div>
          <button class="icon-button" aria-label="关闭助手" @click="open = false">
            <AppIcon name="close" :size="18" />
          </button>
        </header>

        <div ref="body" class="assistant-body">
          <div v-for="(message, index) in messages" :key="index" class="message" :class="`message--${message.role}`">
            <p>{{ message.text }}</p>
            <div v-if="message.links?.length" class="message-links">
              <button v-for="link in message.links" :key="link.label" @click="openLink(link)">
                {{ link.label }} <AppIcon name="arrow" :size="12" />
              </button>
            </div>
          </div>
          <div v-if="thinking" class="message message--bot">
            <p class="thinking">正在查找档案…</p>
          </div>
        </div>

        <div class="assistant-quick">
          <button v-for="question in quickQuestions" :key="question" @click="useQuick(question)">
            {{ question }}
          </button>
        </div>

        <form class="assistant-form" @submit.prevent="ask(input)">
          <textarea v-model="input" rows="2" placeholder="问一条纹样的来路…" @keydown.enter.exact.prevent="ask(input)"></textarea>
          <button type="submit" aria-label="发送问题" :disabled="thinking">
            <AppIcon name="arrow" :size="17" />
          </button>
        </form>
      </section>
    </transition>

    <button class="assistant-trigger" :class="{ 'is-open': open }" @click="open = !open">
      <AppIcon name="chat" :size="19" />
      <span>纹脉助手</span>
    </button>
  </div>
</template>

<style scoped>
.assistant {
  position: fixed;
  z-index: 120;
  right: 24px;
  bottom: 24px;
}

.assistant-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 15px;
  border: 1px solid var(--terracotta);
  border-radius: 999px;
  background: var(--terracotta);
  color: var(--paper-soft);
  font-size: 18px;
  box-shadow: 0 8px 24px rgba(46, 42, 36, 0.2);
  transition: background 0.3s var(--ease), transform 0.3s var(--ease);
}

.assistant-trigger:hover,
.assistant-trigger.is-open {
  background: var(--moss);
  border-color: var(--moss);
  transform: translateY(-2px);
}

.assistant-panel {
  position: absolute;
  right: 0;
  bottom: 55px;
  display: flex;
  width: min(430px, calc(100vw - 32px));
  height: min(620px, calc(100vh - 120px));
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--paper-soft);
  box-shadow: 0 20px 55px rgba(46, 42, 36, 0.2);
}

.assistant-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 17px 13px;
  border-top: 4px solid var(--ochre);
  border-bottom: 1px solid var(--line);
  background: var(--moss-deep);
  color: var(--paper-soft);
}

.assistant-head div {
  display: grid;
  gap: 4px;
}

.assistant-head strong {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 500;
}

.assistant-head .eyebrow {
  color: rgba(242, 241, 236, 0.84);
}

.icon-button {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 0;
  background: transparent;
  color: var(--paper-soft);
}

.assistant-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding: 16px;
}

.message {
  max-width: 88%;
  padding: 9px 11px;
  border-radius: 11px;
  font-size: 18px;
  line-height: 1.8;
}

.message--bot {
  align-self: flex-start;
  border: 1px solid var(--line-soft);
  background: rgba(232, 231, 225, 0.72);
}

.message--user {
  align-self: flex-end;
  background: var(--terracotta);
  color: var(--paper-soft);
}

.message-links {
  display: grid;
  gap: 4px;
  margin-top: 7px;
}

.message-links button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--terracotta);
  font-size: 18px;
  text-align: left;
}

.thinking {
  color: var(--ink-mute);
}

.assistant-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 13px 10px;
}

.assistant-quick button {
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: transparent;
  color: var(--ink-mute);
  font-size: 18px;
}

.assistant-quick button:hover {
  border-color: var(--moss);
  color: var(--accent-strong);
}

.assistant-form {
  display: flex;
  gap: 8px;
  padding: 11px 13px;
  border-top: 1px solid var(--line);
}

.assistant-form textarea {
  flex: 1;
  min-width: 0;
  resize: none;
  border: 0;
  background: transparent;
  font-size: 18px;
  line-height: 1.6;
  outline: none;
}

.assistant-form textarea::placeholder {
  color: var(--ink-mute);
}

.assistant-form button {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  align-self: flex-end;
  border: 1px solid var(--terracotta);
  border-radius: 50%;
  background: var(--terracotta);
  color: var(--paper-soft);
}

.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.3s var(--ease), transform 0.3s var(--ease);
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (max-width: 500px) {
  .assistant {
    right: 14px;
    bottom: 14px;
  }
}
</style>
