import path from 'node:path'
import {
  createSession,
  clearBrowserAuth,
  loginViaUi,
  resolveAdminPassword,
} from './cdp_session.mjs'

const baseUrl = process.argv[2] || 'http://127.0.0.1:5173'
const cdpUrl = process.argv[3] || 'http://127.0.0.1:9223'
const shotDir = path.resolve(process.argv[4] || 'docs/assets/p0-auth')
const apiBase = process.env.API_BASE || 'http://127.0.0.1:8000'
const adminUser = process.env.ADMIN_USER || 'admin'
const adminPassword = resolveAdminPassword()

const results = []
function check(name, ok, detail = '') {
  results.push({ name, ok: Boolean(ok), detail })
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  [${detail}]` : ''}`)
}

async function layoutState(session) {
  return JSON.parse(
    await session.evaluate(`JSON.stringify({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      small: [...document.querySelectorAll('body *')]
        .filter(el => el.children.length === 0 && el.innerText?.trim())
        .map(el => ({ text: el.innerText.trim().slice(0, 18), size: parseFloat(getComputedStyle(el).fontSize) }))
        .filter(item => item.size > 0 && item.size < 18)
        .slice(0, 6)
    })`),
  )
}

const session = await createSession(cdpUrl)

try {
  await session.navigate(`${baseUrl}/`)
  await clearBrowserAuth(session)
  await session.navigate(`${baseUrl}/`)

  const headerGuest = await session.evaluate(
    "document.querySelector('.header-tools')?.innerText || ''",
  )
  check('游客头部显示登录入口', headerGuest.includes('登录 / 注册'))

  await session.navigate(`${baseUrl}/admin`)
  await session.waitFor("location.pathname === '/login'")
  const loginPage = JSON.parse(
    await session.evaluate(`JSON.stringify({
      path: location.pathname,
      search: location.search,
      heading: document.querySelector('.login-intro h1')?.innerText || '',
      body: document.body.innerText
    })`),
  )
  check(
    '未登录访问后台被拦截并带 redirect',
    loginPage.path === '/login' && loginPage.search.includes('redirect'),
    loginPage.search,
  )
  check('登录页标题正确', loginPage.heading.includes('纹样档案'))
  check(
    '登录页不展示管理员口令',
    !loginPage.body.includes('admin123456') && !loginPage.body.includes('演示管理员'),
  )

  const loginLayout = await layoutState(session)
  check('登录页无横向溢出', loginLayout.scrollWidth <= loginLayout.innerWidth + 2)
  check('登录页可见文字 ≥18px', loginLayout.small.length === 0, JSON.stringify(loginLayout.small))
  await session.screenshot(shotDir, 'login-desktop')

  await loginViaUi(
    session,
    baseUrl,
    adminUser,
    adminPassword,
    '/login?redirect=/admin',
  )
  await session.waitFor("location.pathname === '/admin'")
  await session.waitFor("document.body.innerText.includes('系统管理员')")
  const adminState = JSON.parse(
    await session.evaluate(`JSON.stringify({
      heading: document.querySelector('.admin-head h1')?.innerText || '',
      status: document.querySelector('.admin-status')?.innerText || '',
      metrics: [...document.querySelectorAll('.metric strong')].map(el => el.innerText),
      signedIn: document.querySelector('.admin-foot')?.innerText || ''
    })`),
  )
  check('管理员登录后进入后台', adminState.heading === '数据概览', adminState.heading)
  check('后台连接数据库', adminState.status.includes('已连接'), adminState.status)
  check('后台显示当前管理员', adminState.signedIn.includes('系统管理员'))
  check(
    '后台统计来自数据库',
    adminState.metrics[0] === '1346' && adminState.metrics[1] === '1171',
    adminState.metrics.join(','),
  )
  await session.screenshot(shotDir, 'admin-signed-in')

  await session.click('.admin-foot .admin-logout')
  await session.waitFor("location.pathname === '/login'")
  check('管理员退出后回到登录页', true)

  const suffix = Date.now().toString().slice(-7)
  const username = `reader${suffix}`
  const displayName = `验收读者${suffix}`
  await session.navigate(`${baseUrl}/login`)
  await session.waitFor("document.querySelectorAll('.login-tabs .login-tab').length === 2")
  await session.evaluate("document.querySelectorAll('.login-tabs .login-tab')[1].click()")
  await session.waitFor("document.querySelectorAll('.login-form input').length === 5")
  await session.fillVisibleInputs('.login-form', [
    username,
    displayName,
    `${username}@example.com`,
    'reader123456',
    'reader123456',
  ])
  await session.evaluate("document.querySelector('.login-form').requestSubmit()")
  await session.waitFor("location.pathname === '/profile'")
  await session.waitFor(
    `document.querySelector('.profile-identity h1')?.innerText.includes(${JSON.stringify(displayName)})`,
  )
  const profileState = JSON.parse(
    await session.evaluate(`JSON.stringify({
      heading: document.querySelector('.profile-identity h1')?.innerText || '',
      identity: document.querySelector('.profile-identity')?.innerText || '',
      actions: document.querySelector('.profile-actions')?.innerText || ''
    })`),
  )
  check('注册后自动登录进入个人中心', profileState.heading === displayName)
  check('个人中心显示真实账号', profileState.identity.includes(username))
  check(
    '个人中心显示已登录状态与退出入口',
    profileState.identity.includes('已登录读者') && profileState.actions.includes('退出登录'),
  )
  await session.screenshot(shotDir, 'profile-reader')

  await session.navigate(`${baseUrl}/patterns`, 1800)
  await session.waitFor("document.querySelector('.specimen__favorite') !== null")
  const userPatternId = await session.evaluate(
    "document.querySelector('.specimen')?.dataset.patternId || ''",
  )
  await session.evaluate("document.querySelector('.specimen__favorite').click()")
  await session.wait(1400)
  const userToken = await session.evaluate("localStorage.getItem('wenmai:token') || ''")
  const mine = await fetch(`${apiBase}/api/me/favorites`, {
    headers: { Authorization: `Bearer ${userToken}` },
  }).then((response) => response.json())
  check(
    '登录用户收藏写入本人账号',
    mine.items.some((item) => item.id === userPatternId),
    userPatternId,
  )
  const guestView = await fetch(`${apiBase}/api/me/favorites`).then((response) =>
    response.json(),
  )
  check(
    '登录用户收藏不污染游客账号',
    !guestView.items.some((item) => item.id === userPatternId),
  )

  await session.navigate(`${baseUrl}/admin`)
  await session.waitFor("location.pathname === '/profile'")
  const denied = await session.evaluate(
    "document.body.innerText.includes('管理后台需要管理员权限')",
  )
  check('普通用户访问后台被拒绝', denied)

  await session.evaluate(
    "[...document.querySelectorAll('.account button')].find(el => el.innerText.includes('退出'))?.click()",
  )
  await session.waitFor(
    "document.querySelector('.header-tools')?.innerText.includes('登录 / 注册')",
  )
  check('退出登录后头部恢复登录入口', true)

  await session.wait(1500)
  const residue = JSON.parse(
    await session.evaluate(`JSON.stringify({
      token: localStorage.getItem('wenmai:token'),
      favorites: localStorage.getItem('wenmai:favorites') || '[]'
    })`),
  )
  const guestApiFavorites = await fetch(`${apiBase}/api/me/favorites`).then((response) =>
    response.json(),
  )
  const storedFavorites = JSON.parse(residue.favorites || '[]').sort()
  const guestFavoriteIds = guestApiFavorites.items.map((item) => item.id).sort()
  check('退出后清除登录令牌', !residue.token, `token=${Boolean(residue.token)}`)
  check(
    '退出后收藏切换为游客账号',
    JSON.stringify(storedFavorites) === JSON.stringify(guestFavoriteIds),
  )
  await fetch(`${apiBase}/api/me/favorites/${encodeURIComponent(userPatternId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${userToken}` },
  })

  await session.navigate(`${baseUrl}/patterns`, 1800)
  await session.waitFor("document.querySelector('.specimen__favorite') !== null")
  const patternId = await session.evaluate(
    "document.querySelector('.specimen')?.dataset.patternId || ''",
  )
  const countBefore = Number(
    await session.evaluate("Number(document.querySelector('.saved-link span')?.innerText || 0)"),
  )
  await session.evaluate("document.querySelector('.specimen__favorite').click()")
  await session.wait(1400)
  const countAfter = Number(
    await session.evaluate("Number(document.querySelector('.saved-link span')?.innerText || 0)"),
  )
  const guestFavorites = await fetch(`${apiBase}/api/me/favorites`).then((response) =>
    response.json(),
  )
  check(
    '游客收藏写入演示账号',
    guestFavorites.items.some((item) => item.id === patternId),
    `count ${countBefore} → ${countAfter}`,
  )
  await fetch(`${apiBase}/api/me/favorites/${encodeURIComponent(patternId)}`, {
    method: 'DELETE',
  })

  await session.setViewport(390, 844, true)
  await session.navigate(`${baseUrl}/login`)
  const mobileLayout = await layoutState(session)
  check('移动端登录页无横向溢出', mobileLayout.scrollWidth <= mobileLayout.innerWidth + 2)
  check(
    '移动端登录页可见文字 ≥18px',
    mobileLayout.small.length === 0,
    JSON.stringify(mobileLayout.small),
  )
  await session.screenshot(shotDir, 'login-mobile')

  await session.navigate(`${baseUrl}/`)
  const heroNumbers = await session.waitFor(
    `(() => {
      const values = [...document.querySelectorAll('.hero__numbers strong')].map(el => Number(el.innerText))
      return values.length === 1 && values[0] > 0 ? values : false
    })()`,
  )
  const stats = await fetch(`${apiBase}/api/stats`).then((response) => response.json())
  check(
    '首页统计与 /api/stats 一致',
    heroNumbers[0] === stats.total,
    `${heroNumbers.join('/')} vs ${stats.total}`,
  )

  const apiLogin = await fetch(`${apiBase}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: adminUser, password: adminPassword }),
  }).then((response) => response.json())
  const authHeader = { Authorization: `Bearer ${apiLogin.token}` }
  const users = await fetch(`${apiBase}/api/users`, { headers: authHeader }).then(
    (response) => response.json(),
  )
  const created = users.find((item) => item.username === username)
  if (created) {
    await fetch(`${apiBase}/api/users/${created.id}`, {
      method: 'DELETE',
      headers: authHeader,
    })
  }
  const remainingUsers = await fetch(`${apiBase}/api/users`, {
    headers: authHeader,
  }).then((response) => response.json())
  check(
    '验收测试账号已清理',
    !remainingUsers.some((item) => item.username === username),
  )

  await clearBrowserAuth(session)

  const unexpected = session.runtimeErrors.filter(
    (message) => !/favicon|DevTools/i.test(message),
  )
  check('浏览器运行时错误为 0', unexpected.length === 0, unexpected.join(' | '))
} finally {
  session.close()
}

const failed = results.filter((item) => !item.ok)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
if (failed.length) {
  console.log('Failed checks:')
  for (const item of failed) console.log(` - ${item.name} ${item.detail}`)
  process.exitCode = 1
}
