import { createSession, clearBrowserAuth, loginViaUi, resolveAdminPassword } from './cdp_session.mjs'

const baseUrl = process.argv[2] || 'http://127.0.0.1:5173'
const cdpUrl = process.argv[3] || 'http://127.0.0.1:9223'
const adminUser = process.env.ADMIN_USER || 'admin'
const adminPassword = resolveAdminPassword()

const session = await createSession(cdpUrl, { width: 1440, height: 1000 })

try {
  await session.navigate(`${baseUrl}/admin`)
  await clearBrowserAuth(session)
  const { evaluate, wait } = session

  await loginViaUi(session, baseUrl, adminUser, adminPassword, '/login?redirect=/admin')
  await session.waitFor("location.pathname === '/admin'")
  await session.waitFor(
    "document.querySelector('.admin-status')?.innerText.includes('已连接')",
  )

  const overview = JSON.parse(
    await evaluate(`JSON.stringify({
      title: document.querySelector('h1')?.innerText,
      databaseStatus: document.querySelector('.admin-status')?.innerText,
      signedInAs: document.querySelector('.admin-foot')?.innerText || '',
      metricValues: [...document.querySelectorAll('.metric strong')].map(el => el.innerText)
    })`),
  )

  await evaluate(`[...document.querySelectorAll('.admin-nav button')]
    .find(el => el.innerText.includes('纹样档案'))?.click()`)
  await wait(1400)
  const listState = JSON.parse(
    await evaluate(`JSON.stringify({
      rows: document.querySelectorAll('.archive-table tbody tr').length,
      total: document.querySelector('.table-meta')?.innerText,
      hasCreate: [...document.querySelectorAll('button')].some(el => el.innerText.includes('新增纹样'))
    })`),
  )

  await evaluate(`[...document.querySelectorAll('button')]
    .find(el => el.innerText.includes('新增纹样'))?.click()`)
  await wait(300)
  await evaluate(`(() => {
    const label = [...document.querySelectorAll('.editor-form label')]
      .find(el => el.querySelector('span')?.innerText === '纹样名称')
    const input = label?.querySelector('input')
    if (!input) return false
    input.value = '界面 CRUD 测试'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    return true
  })()`)
  await evaluate(`document.querySelector('.editor-form')?.requestSubmit()`)
  await wait(1800)
  const created = await evaluate(`document.body.innerText.includes('界面 CRUD 测试')`)

  await evaluate(`window.confirm = () => true`)
  await evaluate(`(() => {
    const row = [...document.querySelectorAll('.archive-table tbody tr')]
      .find(el => el.innerText.includes('界面 CRUD 测试'))
    const button = row && [...row.querySelectorAll('button')]
      .find(el => el.innerText.includes('删除'))
    if (button) button.click()
    return Boolean(button)
  })()`)
  await wait(1600)
  const cleaned = !(await evaluate(`document.body.innerText.includes('界面 CRUD 测试')`))

  console.log(
    JSON.stringify(
      {
        overview,
        listState,
        created,
        cleaned,
        runtimeErrors: session.runtimeErrors,
      },
      null,
      2,
    ),
  )
} finally {
  session.close()
}
