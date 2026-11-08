import { createSession, clearBrowserAuth } from './cdp_session.mjs'

const baseUrl = process.argv[2] || 'http://127.0.0.1:5173'
const cdpUrl = process.argv[3] || 'http://127.0.0.1:9223'
const apiBase = process.env.API_BASE || 'http://127.0.0.1:8000'

const session = await createSession(cdpUrl, { width: 1440, height: 1000 })

try {
  const { evaluate, wait } = session
  await session.navigate(`${baseUrl}/`)
  await clearBrowserAuth(session)
  await session.navigate(`${baseUrl}/patterns`, 2600)
  await session.waitFor("document.querySelector('.specimen__favorite') !== null")

  const patternId = await evaluate(
    "document.querySelector('.specimen')?.dataset.patternId || ''",
  )
  const before = Number(
    await evaluate("Number(document.querySelector('.saved-link span')?.innerText || 0)"),
  )
  await evaluate("document.querySelector('.specimen__favorite').click()")
  await wait(1500)
  const after = Number(
    await evaluate("Number(document.querySelector('.saved-link span')?.innerText || 0)"),
  )
  const saved = await evaluate(
    "document.querySelector('.specimen__favorite')?.classList.contains('is-saved') || false",
  )

  await session.navigate(`${baseUrl}/profile`, 1600)
  const profileState = JSON.parse(
    await evaluate(`JSON.stringify({
      favorites: document.querySelectorAll('.profile-grid .specimen').length,
      historyRows: document.querySelectorAll('.history-row').length,
      heading: document.querySelector('.profile-identity h1')?.innerText || ''
    })`),
  )

  const apiFavorites = await fetch(`${apiBase}/api/me/favorites`).then((response) =>
    response.json(),
  )
  const storedInDemo = apiFavorites.items.some((item) => item.id === patternId)

  await fetch(`${apiBase}/api/me/favorites/${encodeURIComponent(patternId)}`, {
    method: 'DELETE',
  })

  console.log(
    JSON.stringify(
      {
        patternId,
        before,
        after,
        saved,
        profileState,
        storedInDemo,
        cleaned: true,
        runtimeErrors: session.runtimeErrors,
      },
      null,
      2,
    ),
  )
} finally {
  session.close()
}
