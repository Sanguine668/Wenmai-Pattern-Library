import path from 'node:path'
import { createSession } from './cdp_session.mjs'

const baseUrl = process.argv[2] || 'http://127.0.0.1:5173'
const cdpUrl = process.argv[3] || 'http://127.0.0.1:9223'
const shotDir = path.resolve(process.argv[4] || 'docs/assets/ui-2026-11-08')

const session = await createSession(cdpUrl, { width: 1440, height: 1000 })

try {
  await session.navigate(`${baseUrl}/`, 1400)
  const homeTop = JSON.parse(
    await session.evaluate(`JSON.stringify({
      headerHeight: document.querySelector('.header-inner')?.getBoundingClientRect().height,
      headerWidth: document.querySelector('.header-inner')?.getBoundingClientRect().width,
      brand: document.querySelector('.brand')?.innerText,
      icon: (() => { const img = document.querySelector('.brand__icon'); return img ? { width: img.getBoundingClientRect().width, loaded: img.complete && img.naturalWidth > 0 } : null })(),
      nav: [...document.querySelectorAll('.desktop-nav .nav-link')].map(el => ({ text: el.innerText, active: el.classList.contains('is-active') })),
      heroNumbers: [...document.querySelectorAll('.hero__numbers strong')].map(el => el.innerText),
      account: document.querySelector('.account')?.innerText
    })`),
  )
  console.log('home-top', JSON.stringify(homeTop))
  await session.screenshot(shotDir, 'home-top')

  await session.evaluate("document.querySelector('.index-section')?.scrollIntoView({ block: 'center' })")
  await session.wait(600)
  const indexState = JSON.parse(
    await session.evaluate(`JSON.stringify({
      items: [...document.querySelectorAll('.index-item')].map(el => ({
        no: el.querySelector('.index-item__no')?.innerText,
        name: el.querySelector('.index-item__name')?.innerText,
        count: el.querySelector('.index-item__count')?.innerText
      })),
      overlap: [...document.querySelectorAll('.index-item')].filter(el => {
        const no = el.querySelector('.index-item__no')?.getBoundingClientRect()
        const thumb = el.querySelector('.index-item__thumb')?.getBoundingClientRect()
        if (!no || !thumb) return false
        return !(no.right <= thumb.left || no.left >= thumb.right || no.bottom <= thumb.top || no.top >= thumb.bottom)
      }).length,
      footnote: document.querySelector('.index-footnote')?.innerText
    })`),
  )
  console.log('home-index', JSON.stringify(indexState))
  await session.screenshot(shotDir, 'home-index')

  await session.navigate(`${baseUrl}/login`, 1400)
  const loginState = JSON.parse(
    await session.evaluate(`JSON.stringify({
      ledger: [...document.querySelectorAll('.login-ledger strong')].map(el => el.innerText),
      plates: [...document.querySelectorAll('.login-plate')].map(el => el.querySelector('strong')?.innerText),
      pageHeight: document.body.scrollHeight,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth
    })`),
  )
  console.log('login', JSON.stringify(loginState))
  await session.screenshot(shotDir, 'login-top')
  await session.evaluate("document.querySelector('.login-plates')?.scrollIntoView({ block: 'start' })")
  await session.wait(500)
  await session.screenshot(shotDir, 'login-plates')

  await session.navigate(`${baseUrl}/patterns`, 2000)
  const patternsState = JSON.parse(
    await session.evaluate(`JSON.stringify({
      motifs: [...document.querySelectorAll('.filter-list')[0].querySelectorAll('.filter-option')].map(el => el.innerText.replace('\\n', ' ')),
      pageButtons: [...document.querySelectorAll('.pagination__page')].map(el => el.innerText),
      summary: document.querySelector('.pagination__summary')?.innerText,
      total: document.querySelector('.library-toolbar strong')?.innerText
    })`),
  )
  console.log('patterns-top', JSON.stringify(patternsState))
  await session.screenshot(shotDir, 'patterns-top')
  await session.evaluate("document.querySelector('.pagination')?.scrollIntoView({ block: 'center' })")
  await session.wait(400)
  await session.screenshot(shotDir, 'patterns-pagination')

  await session.setViewport(390, 844, true)
  await session.navigate(`${baseUrl}/`, 1400)
  await session.screenshot(shotDir, 'home-mobile')
  const mobileHome = JSON.parse(
    await session.evaluate(`JSON.stringify({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      header: document.querySelector('.header-inner')?.getBoundingClientRect().height,
      indexItems: document.querySelectorAll('.index-item').length
    })`),
  )
  console.log('home-mobile', JSON.stringify(mobileHome))

  await session.navigate(`${baseUrl}/patterns`, 2000)
  const mobilePatterns = JSON.parse(
    await session.evaluate(`JSON.stringify({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      pagination: document.querySelectorAll('.pagination__page').length
    })`),
  )
  console.log('patterns-mobile', JSON.stringify(mobilePatterns))
  await session.screenshot(shotDir, 'patterns-mobile')

  await session.navigate(`${baseUrl}/login`, 1400)
  const mobileLogin = JSON.parse(
    await session.evaluate(`JSON.stringify({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      plates: document.querySelectorAll('.login-plate').length
    })`),
  )
  console.log('login-mobile', JSON.stringify(mobileLogin))
  await session.screenshot(shotDir, 'login-mobile')

  const small = JSON.parse(
    await session.evaluate(`JSON.stringify([...document.querySelectorAll('body *')]
      .filter(el => el.children.length === 0 && el.innerText?.trim())
      .map(el => ({ text: el.innerText.trim().slice(0, 16), size: parseFloat(getComputedStyle(el).fontSize) }))
      .filter(item => item.size > 0 && item.size < 18)
      .slice(0, 8))`),
  )
  console.log('small-text', JSON.stringify(small))
  console.log('runtime-errors', JSON.stringify(session.runtimeErrors))
} finally {
  session.close()
}
