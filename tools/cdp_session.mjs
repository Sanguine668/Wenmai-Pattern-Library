import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export function resolveAdminPassword() {
  if (process.env.ADMIN_PASSWORD) return process.env.ADMIN_PASSWORD
  try {
    const here = path.dirname(fileURLToPath(import.meta.url))
    const file = path.resolve(here, '..', 'data', 'admin-initial-password.txt')
    const value = fs.readFileSync(file, 'utf8').trim()
    if (value) return value
  } catch {
    // Fall through to an explicit error below.
  }
  throw new Error(
    '未找到管理员密码：请设置 ADMIN_PASSWORD，或运行 ' +
      'python -m app.admin_tool set-password --generate 生成 data/admin-initial-password.txt',
  )
}

export async function createSession(cdpUrl, options = {}) {
  const {
    width = 1440,
    height = 1000,
    mobile = false,
    waitMs = 700,
  } = options
  const targets = await fetch(`${cdpUrl}/json`).then((response) => response.json())
  const page = targets.find((item) => item.type === 'page')
  if (!page) throw new Error('No page target found')

  const socket = new WebSocket(page.webSocketDebuggerUrl)
  const pending = new Map()
  const runtimeErrors = []
  let nextId = 0

  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      const job = pending.get(message.id)
      pending.delete(message.id)
      if (message.error) job.reject(new Error(message.error.message))
      else job.resolve(message.result)
      return
    }
    if (message.method === 'Runtime.exceptionThrown') {
      runtimeErrors.push(
        message.params?.exceptionDetails?.exception?.description ||
          message.params?.exceptionDetails?.text ||
          'runtime exception',
      )
    }
  })

  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })

  function send(method, params = {}) {
    const id = ++nextId
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject })
      socket.send(JSON.stringify({ id, method, params }))
    })
  }

  async function evaluate(expression, awaitPromise = true) {
    const result = await send('Runtime.evaluate', {
      expression,
      awaitPromise,
      returnByValue: true,
    })
    if (result.exceptionDetails) {
      const detail =
        result.exceptionDetails.exception?.description ||
        result.exceptionDetails.text ||
        'evaluate failed'
      throw new Error(detail)
    }
    return result.result.value
  }

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

  async function setViewport(nextWidth, nextHeight, isMobile = false) {
    await send('Emulation.setDeviceMetricsOverride', {
      width: nextWidth,
      height: nextHeight,
      deviceScaleFactor: 1,
      mobile: isMobile,
    })
  }

  async function waitFor(expression, { timeout = 9000, interval = 160 } = {}) {
    const startedAt = Date.now()
    let last
    while (Date.now() - startedAt < timeout) {
      last = await evaluate(expression)
      if (last) return last
      await wait(interval)
    }
    throw new Error(`waitFor timeout: ${expression} (last=${JSON.stringify(last)})`)
  }

  async function navigate(url, extraWait = waitMs) {
    await send('Page.navigate', { url })
    await waitFor("document.readyState === 'complete'", { timeout: 12000 }).catch(
      () => {},
    )
    await wait(extraWait)
  }

  async function click(selector) {
    const clicked = await evaluate(`(() => {
      const el = document.querySelector(${JSON.stringify(selector)})
      if (!el) return false
      el.click()
      return true
    })()`)
    if (!clicked) throw new Error(`click target missing: ${selector}`)
    return clicked
  }

  async function fillVisibleInputs(scopeSelector, values) {
    return evaluate(`(() => {
      const values = ${JSON.stringify(values)}
      const scope = document.querySelector(${JSON.stringify(scopeSelector)})
      if (!scope) return 0
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
      const inputs = [...scope.querySelectorAll('input')].filter(
        (input) => input.type !== 'hidden' && input.offsetParent !== null,
      )
      inputs.forEach((input, index) => {
        if (values[index] === undefined) return
        setter.call(input, values[index])
        input.dispatchEvent(new Event('input', { bubbles: true }))
      })
      return inputs.length
    })()`)
  }

  async function screenshot(directory, name) {
    fs.mkdirSync(directory, { recursive: true })
    const shot = await send('Page.captureScreenshot', {
      format: 'png',
      fromSurface: true,
    })
    const target = path.join(directory, `${name}.png`)
    fs.writeFileSync(target, Buffer.from(shot.data, 'base64'))
    return target
  }

  function close() {
    try {
      socket.close()
    } catch {
      // Socket already closed.
    }
  }

  await send('Runtime.enable')
  await send('Page.enable')
  await setViewport(width, height, mobile)

  return {
    send,
    evaluate,
    wait,
    waitFor,
    navigate,
    click,
    fillVisibleInputs,
    screenshot,
    setViewport,
    runtimeErrors,
    close,
  }
}

export async function clearBrowserAuth(session) {
  await session.evaluate("localStorage.removeItem('wenmai:token')")
}

export async function loginViaUi(
  session,
  baseUrl,
  username,
  password,
  loginPath = '/login',
) {
  await session.navigate(`${baseUrl}${loginPath}`)
  await session.waitFor("document.querySelector('.login-form') !== null")
  const filled = await session.fillVisibleInputs('.login-form', [username, password])
  if (filled < 2) throw new Error(`login form inputs not found (filled=${filled})`)
  await session.evaluate("document.querySelector('.login-form').requestSubmit()")
  return session.waitFor("location.pathname !== '/login'", { timeout: 10000 })
}
