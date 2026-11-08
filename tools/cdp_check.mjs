import fs from 'node:fs'
import path from 'node:path'

const baseUrl = process.argv[2] || 'http://127.0.0.1:5174'
const cdpUrl = process.argv[3] || 'http://127.0.0.1:9223'
const shotDir = path.resolve(process.argv[4] || 'docs/assets/frontend-preview')
const viewportWidth = Number(process.env.VIEWPORT_WIDTH || 1440)
const viewportHeight = Number(process.env.VIEWPORT_HEIGHT || 1000)
const isMobile = process.env.MOBILE === '1'
const waitMs = Number(process.env.WAIT_MS || 1600)
fs.mkdirSync(shotDir, { recursive: true })

const targets = await fetch(`${cdpUrl}/json`).then((r) => r.json())
const page = targets.find((item) => item.type === 'page')
if (!page) throw new Error('No page target found')

const ws = new WebSocket(page.webSocketDebuggerUrl)
const pending = new Map()
let nextId = 0
const runtimeErrors = []

ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data)
  if (data.id && pending.has(data.id)) {
    const { resolve, reject } = pending.get(data.id)
    pending.delete(data.id)
    if (data.error) reject(new Error(data.error.message))
    else resolve(data.result)
    return
  }
  if (data.method === 'Runtime.exceptionThrown') {
    runtimeErrors.push(data.params?.exceptionDetails?.text || 'runtime exception')
  }
})

await new Promise((resolve) => ws.addEventListener('open', resolve, { once: true }))

function send(method, params = {}) {
  const id = ++nextId
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject })
    ws.send(JSON.stringify({ id, method, params }))
  })
}

await send('Runtime.enable')
await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', {
  width: viewportWidth,
  height: viewportHeight,
  deviceScaleFactor: 1,
  mobile: isMobile,
})

const routes = [
  ['home', '/'],
  ['patterns', '/patterns'],
  ['detail', '/patterns/cleveland-119906'],
  ['upload', '/upload'],
  ['create', '/create'],
  ['profile', '/profile'],
  ['login', '/login'],
].filter(([name]) => !process.env.ONLY || process.env.ONLY.split(',').includes(name))

for (const [name, route] of routes) {
  const before = runtimeErrors.length
  await send('Page.navigate', { url: `${baseUrl}${route}` })
  await new Promise((resolve) => setTimeout(resolve, waitMs))

  const result = await send('Runtime.evaluate', {
    expression: `JSON.stringify({
      title: document.title,
      h1: document.querySelector('h1')?.innerText || '',
      bodyText: document.body.innerText.slice(0, 160),
      cards: document.querySelectorAll('.specimen').length,
      images: [...document.images].filter(img => img.complete && img.naturalWidth > 0).length,
      brokenImages: [...document.images].filter(img => img.complete && img.naturalWidth === 0).length,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      bodyHeight: document.body.scrollHeight,
      filterStyle: (() => {
        const el = document.querySelector('.filter-rail')
        if (!el) return null
        const style = getComputedStyle(el)
        return {
          overflowY: style.overflowY,
          maxHeight: style.maxHeight,
          scrollable: el.scrollHeight > el.clientHeight,
        }
      })(),
      dynastyOrder: [...document.querySelectorAll('.dynasty-item strong')].map(el => el.innerText),
      carousel: (() => {
        const el = document.querySelector('.feature-rail')
        if (!el) return null
        return { scrollable: el.scrollWidth > el.clientWidth, children: el.children.length }
      })(),
      heroGeometry: (() => {
        const copy = document.querySelector('.hero__copy')
        const heading = document.querySelector('.hero h1')
        const intro = document.querySelector('.hero__intro')
        const plate = document.querySelector('.hero__plate')
        if (!copy || !heading || !intro || !plate) return null
        const copyRect = copy.getBoundingClientRect()
        const headingRect = heading.getBoundingClientRect()
        const introRect = intro.getBoundingClientRect()
        const plateRect = plate.getBoundingClientRect()
        return {
          copyWidth: Math.round(copyRect.width),
          headingRight: Math.round(headingRect.right),
          introRight: Math.round(introRect.right),
          plateLeft: Math.round(plateRect.left),
          plateWidth: Math.round(plateRect.width),
          visibleGap: Math.round(plateRect.left - Math.max(headingRect.right, introRect.right)),
        }
      })(),
      smallTexts: [...document.querySelectorAll('body *')]
        .filter(el => el.children.length === 0 && el.innerText?.trim())
        .map(el => ({ text: el.innerText.trim().slice(0, 24), size: parseFloat(getComputedStyle(el).fontSize) }))
        .filter(item => item.size > 0 && item.size < 18)
        .slice(0, 8)
    })`,
    returnByValue: true,
  })
  const data = JSON.parse(result.result.value)
  const overflow = data.scrollWidth > data.innerWidth + 2
  console.log(
    `${name.padEnd(9)} | h1=${data.h1 || '-'} | cards=${data.cards} | images=${data.images} broken=${data.brokenImages} | overflow=${overflow} | smallText=${data.smallTexts.length} | errors=${runtimeErrors.length - before}`,
  )
  if (!data.h1) console.log('  body:', data.bodyText)
  if (data.smallTexts.length) console.log('  small:', data.smallTexts)
  if (data.filterStyle) console.log('  filter:', data.filterStyle)
  if (data.dynastyOrder.length) console.log('  dynasty:', data.dynastyOrder)
  if (data.carousel) console.log('  carousel:', data.carousel)
  if (data.heroGeometry) console.log('  hero:', data.heroGeometry)
  if (process.env.SHOT === '1' && ['home', 'patterns', 'detail'].includes(name)) {
    const shot = await send('Page.captureScreenshot', { format: 'png', fromSurface: true })
    const suffix = isMobile ? '-mobile' : ''
    try {
      fs.writeFileSync(path.join(shotDir, `${name}${suffix}.png`), Buffer.from(shot.data, 'base64'))
    } catch {
      console.log(`  screenshot skipped: ${name}${suffix}.png`)
    }
  }
}

if (runtimeErrors.length) {
  console.log('Runtime errors:', runtimeErrors)
}
ws.close()
