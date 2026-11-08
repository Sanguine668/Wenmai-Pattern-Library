const base = process.argv[2] || 'http://127.0.0.1:5175'
const cdp = process.argv[3] || 'http://127.0.0.1:9223'

const targets = await fetch(`${cdp}/json`).then((r) => r.json())
const page = targets.find((item) => item.type === 'page')
const ws = new WebSocket(page.webSocketDebuggerUrl)
const pending = new Map()
let nextId = 0
ws.addEventListener('message', (event) => {
  const msg = JSON.parse(event.data)
  if (!msg.id) return
  const job = pending.get(msg.id)
  if (!job) return
  pending.delete(msg.id)
  msg.error ? job.reject(new Error(msg.error.message)) : job.resolve(msg.result)
})
await new Promise((resolve) => ws.addEventListener('open', resolve, { once: true }))
const send = (method, params = {}) =>
  new Promise((resolve, reject) => {
    const id = ++nextId
    pending.set(id, { resolve, reject })
    ws.send(JSON.stringify({ id, method, params }))
  })

await send('Runtime.enable')
await send('Page.enable')
await send('Page.navigate', { url: `${base}/patterns` })
await new Promise((resolve) => setTimeout(resolve, 1800))
const result = await send('Runtime.evaluate', {
  expression: `(async () => {
    const target = [...document.querySelectorAll('.filter-option')]
      .find(el => el.innerText.includes('漆器'))
    if (!target) return JSON.stringify({ error: 'filter not found' })
    target.click()
    await new Promise(resolve => setTimeout(resolve, 500))
    return JSON.stringify({
      chip: target.innerText,
      count: document.querySelector('.library-toolbar strong')?.innerText,
      cards: document.querySelectorAll('.library-grid .specimen').length
    })
  })()`,
  awaitPromise: true,
  returnByValue: true,
})
console.log(result.result.value)
ws.close()
