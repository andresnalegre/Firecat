const { app, BrowserWindow, shell, session, ipcMain, net } = require('electron')
const { spawn, spawnSync } = require('child_process')
const path = require('path')
const http = require('http')
const os   = require('os')
const fs   = require('fs')

app.commandLine.appendSwitch('ignore-certificate-errors')
app.commandLine.appendSwitch('allow-insecure-localhost')
app.commandLine.appendSwitch('disable-web-security')
app.commandLine.appendSwitch('allow-running-insecure-content')
app.commandLine.appendSwitch('ssl-version-min', 'tls1')
app.commandLine.appendSwitch('cipher-suite-blacklist', '')
app.commandLine.appendSwitch('disable-features', 'BlockInsecurePrivateNetworkRequests,InsecureDownloadWarnings')

let mainWindow
let searchWorkerWindow
let djangoProcess

const DJANGO_PORT     = 8765
const DOWNLOADS_DIR   = path.join(os.homedir(), 'Downloads')
const EXTERNAL_DJANGO = Boolean(process.env.FIRECAT_EXTERNAL_DJANGO)

const downloadSessionsSetup = new WeakSet()

// ---------------------------------------------------------------------------
// Search worker — invisible BrowserWindow that does real browser searches
// ---------------------------------------------------------------------------

// Queue of pending search requests
const searchQueue   = []
let   searchBusy    = false

function createSearchWorker() {
  searchWorkerWindow = new BrowserWindow({
    width:  1280,
    height: 800,
    show:   false,   // invisible
    webPreferences: {
      nodeIntegration:             false,
      contextIsolation:            true,
      webSecurity:                 false,
      allowRunningInsecureContent: true,
      // Use the default session — it has network access and real cookies
      // This is what makes Google work: same session as a real browser
    },
  })

  // Configure session — bypass SSL errors, strip security headers
  const workerSession = searchWorkerWindow.webContents.session
  workerSession.setCertificateVerifyProc((req, cb) => cb(0))
  workerSession.webRequest.onHeadersReceived((details, callback) => {
    const headers = { ...details.responseHeaders }
    delete headers['x-frame-options']
    delete headers['X-Frame-Options']
    delete headers['content-security-policy']
    delete headers['Content-Security-Policy']
    callback({ responseHeaders: headers })
  })

  searchWorkerWindow.on('closed', () => {
    searchWorkerWindow = null
  })

  safeLog('[SearchWorker] Created')
}

function ensureSearchWorker() {
  if (!searchWorkerWindow || searchWorkerWindow.isDestroyed()) {
    createSearchWorker()
  }
}

/**
 * Execute a real browser search in the invisible window.
 * Returns the extracted HTML of results.
 *
 * @param {string} engine  'google' | 'bing' | 'ddg' | 'startpage'
 * @param {string} query
 * @returns {Promise<string>}  raw HTML of results page
 */
function browserSearch(engine, query) {
  return new Promise((resolve) => {
    ensureSearchWorker()

    const urls = {
      google:    `https://www.google.com/search?q=${encodeURIComponent(query)}&hl=en&num=20&pws=0`,
      bing:      `https://www.bing.com/search?q=${encodeURIComponent(query)}&setlang=en-US&count=20`,
      ddg:       `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}&kl=en-us`,
      startpage: `https://www.startpage.com/sp/search?q=${encodeURIComponent(query)}&language=english`,
    }

    const url    = urls[engine] || urls.google
    let resolved = false

    searchWorkerWindow.webContents.setMaxListeners(100)

    const done = (html) => {
      if (resolved) return
      resolved = true
      clearTimeout(timer)
      searchWorkerWindow.webContents.removeListener('did-finish-load', onFinish)
      searchWorkerWindow.webContents.removeListener('did-fail-load', onFail)
      safeLog(`[SearchWorker] Got ${(html || '').length} chars from ${engine}`)
      resolve(html || '')
    }

    const extractHTML = () => {
      if (resolved) return
      searchWorkerWindow.webContents
        .executeJavaScript('document.documentElement.outerHTML')
        .then(html => done(html))
        .catch(() => done(''))
    }

    const onFinish = () => setTimeout(extractHTML, 2500)
    const onFail   = (e, code) => {
      safeLog(`[SearchWorker] Load failed ${code}`)
      setTimeout(extractHTML, 500)
    }

    const timer = setTimeout(() => {
      safeLog(`[SearchWorker] Timeout ${engine} — ${query.slice(0, 40)}`)
      done('')
    }, 30000)

    searchWorkerWindow.webContents.once('did-finish-load', onFinish)
    searchWorkerWindow.webContents.once('did-fail-load', onFail)
    searchWorkerWindow.loadURL(url)
  })
}

/**
 * Process one item from the search queue.
 */
// Track request counts per engine to implement rate limiting
const engineRequestCount = { google: 0, bing: 0, ddg: 0, startpage: 0 }
const ENGINE_COOLDOWN_MS  = 1500  // ms between requests to same engine
const ENGINE_BURST_LIMIT  = 8     // requests before forced cooldown
const ENGINE_BURST_PAUSE  = 5000  // ms pause after burst

async function processSearchQueue() {
  if (searchBusy || searchQueue.length === 0) return
  searchBusy = true

  const { engine, query, resolve } = searchQueue.shift()
  const eng = engine || 'google'

  // Increment counter and check burst limit
  engineRequestCount[eng] = (engineRequestCount[eng] || 0) + 1
  const needsCooldown = engineRequestCount[eng] > 0 && engineRequestCount[eng] % ENGINE_BURST_LIMIT === 0

  try {
    const html = await browserSearch(eng, query)
    resolve(html)
  } catch (err) {
    resolve('')
  } finally {
    searchBusy = false
    // Longer pause after a burst to avoid bot detection
    const delay = needsCooldown ? ENGINE_BURST_PAUSE : ENGINE_COOLDOWN_MS
    if (needsCooldown) safeLog(`[SearchWorker] Burst cooldown ${delay}ms for ${eng}`)
    setTimeout(processSearchQueue, delay)
  }
}

/**
 * Enqueue a search — serialised to avoid parallel loads in the same window.
 */
function queueSearch(engine, query) {
  return new Promise((resolve) => {
    // Deduplicate: skip if identical request already queued
    const isDupe = searchQueue.some(item => item.engine === engine && item.query === query)
    if (isDupe) {
      safeLog(`[SearchWorker] Dedup skip: ${engine} → ${query.slice(0, 40)}`)
      resolve('')
      return
    }
    searchQueue.push({ engine, query, resolve })
    processSearchQueue()
  })
}

// ---------------------------------------------------------------------------
// IPC — Django backend calls these via HTTP on localhost
// ---------------------------------------------------------------------------

// The Django backend sends a POST to /api/search/electron-search/
// We handle it here by doing a real browser search and returning HTML.
// This is a local-only endpoint served by a tiny http server.

const WORKER_PORT = 8766

function startWorkerServer() {
  const server = http.createServer(async (req, res) => {
    // Health check — Django uses this to detect if worker is available
    if (req.url === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: true }))
      return
    }

    if (req.method !== 'POST' || req.url !== '/search') {
      res.writeHead(404)
      res.end()
      return
    }

    let body = ''
    req.on('data', chunk => { body += chunk })
    req.on('end', async () => {
      try {
        const { engine, query } = JSON.parse(body)
        if (!query) {
          res.writeHead(400)
          res.end(JSON.stringify({ error: 'No query' }))
          return
        }

        safeLog(`[SearchWorker] ${engine} → ${query}`)
        const html = await queueSearch(engine || 'google', query)

        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ html, engine, query }))
      } catch (err) {
        safeLog('[SearchWorker] Error:', err.message)
        res.writeHead(500)
        res.end(JSON.stringify({ error: err.message }))
      }
    })
  })

  server.listen(WORKER_PORT, '127.0.0.1', () => {
    safeLog(`[SearchWorker] Worker server listening on port ${WORKER_PORT}`)
  })

  server.on('error', (err) => {
    safeLog('[SearchWorker] Server error:', err.message)
  })
}

// ---------------------------------------------------------------------------
// Existing helpers (unchanged)
// ---------------------------------------------------------------------------

function getPython(backendDir) {
  const candidates = [
    path.join(backendDir, 'venv', 'bin', 'python3'),
    path.join(backendDir, 'venv', 'bin', 'python'),
    '/opt/homebrew/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    'python3',
  ]
  for (const p of candidates) {
    try {
      if (fs.existsSync(p)) {
        try { process.stdout.write(`[Firecat] Found Python at: ${p}\n`) } catch {}
        return p
      }
    } catch {}
  }
  return 'python3'
}

function freePort(port) {
  try {
    spawnSync('bash', ['-c', `lsof -ti:${port} | xargs kill -9 2>/dev/null || true`], { stdio: 'ignore' })
  } catch {}
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const srv = require('net').createServer()
    srv.once('error', () => resolve(false))
    srv.once('listening', () => { srv.close(); resolve(true) })
    srv.listen(port)
  })
}

function uniqueSavePath(dir, filename) {
  const ext  = path.extname(filename)
  const base = path.basename(filename, ext)
  let candidate = path.join(dir, filename)
  let counter = 1
  while (fs.existsSync(candidate)) {
    candidate = path.join(dir, `${base} (${counter})${ext}`)
    counter++
  }
  return candidate
}

function safeLog(...args) {
  try { process.stdout.write(args.join(' ') + '\n') } catch {}
}

function killDjango() {
  if (!djangoProcess) return
  try {
    djangoProcess.kill('SIGTERM')
    const killTimer = setTimeout(() => {
      if (djangoProcess) {
        safeLog('[Firecat] Django did not exit, forcing SIGKILL...')
        try { djangoProcess.kill('SIGKILL') } catch {}
      }
    }, 2000)
    killTimer.unref()
  } catch {}
  djangoProcess = null
}

function startDjango() {
  const backendDir = app.isPackaged
    ? path.join(process.resourcesPath, 'backend')
    : path.join(__dirname, '..', 'backend')

  const python = getPython(backendDir)
  const manage = path.join(backendDir, 'manage.py')

  safeLog('[Firecat] app.isPackaged:', app.isPackaged)
  safeLog('[Firecat] backendDir:', backendDir)
  safeLog('[Firecat] manage.py exists:', fs.existsSync(manage))
  safeLog('[Firecat] Starting Django with:', python)

  djangoProcess = spawn(
    python,
    [manage, 'runserver', `127.0.0.1:${DJANGO_PORT}`, '--noreload'],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        DJANGO_SETTINGS_MODULE:  'firecat_project.settings',
        PYTHONUNBUFFERED:        '1',
        PYTHONPATH:              backendDir,
        FIRECAT_FRONTEND_DIST:   app.isPackaged
          ? path.join(process.resourcesPath, 'frontend_dist')
          : path.join(__dirname, '..', 'frontend', 'dist'),
        FIRECAT_WORKER_PORT:     String(WORKER_PORT),  // tell Django where to find the worker
      },
    }
  )

  djangoProcess.stdout.on('data', d => { try { safeLog('[Django]', d.toString().trim()) } catch {} })
  djangoProcess.stderr.on('data', d => { try { safeLog('[Django]', d.toString().trim()) } catch {} })
  djangoProcess.on('error', err => { try { safeLog('[Django] Error:', err.message) } catch {} })
  djangoProcess.on('exit', code => {
    try { safeLog('[Django] Exit:', code) } catch {}
    djangoProcess = null
  })
}

function waitForDjango(maxRetries = 120) {
  return new Promise((resolve, reject) => {
    let retries  = 0
    let resolved = false

    const check = () => {
      if (resolved) return
      const req = http.get(`http://127.0.0.1:${DJANGO_PORT}/api/bookmarks/`, res => {
        if (resolved) return
        if (res.statusCode < 500) {
          resolved = true
          safeLog(`[Firecat] Django ready! (status ${res.statusCode})`)
          resolve()
        } else {
          retries++
          if (retries >= maxRetries) { reject(new Error('Django timeout')); return }
          setTimeout(check, 500)
        }
        res.resume()
      })
      req.on('error', () => {
        if (resolved) return
        retries++
        if (retries >= maxRetries) { reject(new Error('Django timeout')); return }
        setTimeout(check, 500)
      })
      req.setTimeout(800, () => {
        req.destroy()
        if (resolved) return
        retries++
        if (retries >= maxRetries) { reject(new Error('Django timeout')); return }
        setTimeout(check, 500)
      })
    }

    setTimeout(check, 3000)
  })
}

function setupSession(sess) {
  sess.setCertificateVerifyProc((request, callback) => callback(0))
  sess.webRequest.onHeadersReceived((details, callback) => {
    const headers = { ...details.responseHeaders }
    delete headers['x-frame-options']
    delete headers['X-Frame-Options']
    delete headers['content-security-policy']
    delete headers['Content-Security-Policy']
    callback({ responseHeaders: headers })
  })
}

function setupDownloads(sess) {
  if (downloadSessionsSetup.has(sess)) return
  downloadSessionsSetup.add(sess)

  sess.on('will-download', (event, item) => {
    const fileName   = item.getFilename()
    const savePath   = uniqueSavePath(DOWNLOADS_DIR, fileName)
    const savedName  = path.basename(savePath)
    const downloadId = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`

    item.setSavePath(savePath)
    safeLog('[Firecat] Downloading:', savedName, '→', savePath)

    item.on('updated', (event, state) => {
      if (state === 'progressing' && mainWindow) {
        mainWindow.webContents.send('download-progress', {
          id: downloadId, filename: savedName,
          received: item.getReceivedBytes(), total: item.getTotalBytes(),
          state: 'progressing', savePath,
        })
      }
    })

    item.once('done', (event, state) => {
      safeLog('[Firecat] Download', state, ':', savedName)
      if (mainWindow) {
        mainWindow.webContents.send('download-progress', {
          id: downloadId, filename: savedName,
          received: item.getTotalBytes(), total: item.getTotalBytes(),
          state, savePath,
        })
      }
    })
  })
}

async function clearAllSessions() {
  const storages = [
    'cookies', 'filesystem', 'indexdb', 'localstorage',
    'shadercache', 'websql', 'serviceworkers', 'cachestorage',
  ]
  const sessions = [
    session.defaultSession,
    session.fromPartition('persist:firecat'),
  ]
  for (const sess of sessions) {
    try { await sess.clearCache() } catch {}
    try { await sess.clearStorageData({ storages }) } catch {}
    try { await sess.clearAuthCache() } catch {}
    try { await sess.clearHostResolverCache() } catch {}
  }
  safeLog('[Firecat] Cache and cookies cleared')
}

async function createWindow() {
  setupSession(session.defaultSession)
  setupDownloads(session.defaultSession)

  const webviewSession = session.fromPartition('persist:firecat')
  setupSession(webviewSession)
  setupDownloads(webviewSession)

  mainWindow = new BrowserWindow({
    width:           1400,
    height:          900,
    minWidth:        800,
    minHeight:       600,
    titleBarStyle:   'hiddenInset',
    trafficLightPosition: { x: 16, y: 14 },
    backgroundColor: '#0f0f0f',
    show:            false,
    webPreferences: {
      preload:                     path.join(__dirname, 'preload.js'),
      nodeIntegration:             false,
      contextIsolation:            true,
      webSecurity:                 false,
      webviewTag:                  true,
      allowRunningInsecureContent: true,
    },
  })

  mainWindow.on('enter-full-screen', () => mainWindow.webContents.send('fullscreen-change', true))
  mainWindow.on('leave-full-screen', () => mainWindow.webContents.send('fullscreen-change', false))

  app.on('web-contents-created', (event, contents) => {
    if (contents.getType() === 'webview') {
      setupSession(contents.session)
      setupDownloads(contents.session)
    }
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(`http://127.0.0.1:${DJANGO_PORT}`)) return { action: 'allow' }
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(`http://127.0.0.1:${DJANGO_PORT}`)) {
      event.preventDefault()
    }
  })

  mainWindow.once('ready-to-show', () => mainWindow.show())

  try {
    if (!EXTERNAL_DJANGO) await waitForDjango()
    mainWindow.loadURL(`http://127.0.0.1:${DJANGO_PORT}`)
  } catch (err) {
    safeLog('[Firecat] Backend failed:', err.message)
    mainWindow.loadURL(
      `data:text/html,<h2 style="font-family:sans-serif;color:red;padding:40px">` +
      `Backend failed to start.<br><small>${err.message}</small></h2>`
    )
    mainWindow.show()
  }
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    event.preventDefault()
    callback(true)
  })

  ipcMain.on('open-downloads', () => shell.openPath(DOWNLOADS_DIR))

  ipcMain.handle('clear-cache', async () => {
    await clearAllSessions()
    return { success: true }
  })

  ipcMain.on('open-devtools', () => {
    if (!mainWindow) return
    if (mainWindow.webContents.isDevToolsOpened()) {
      mainWindow.webContents.closeDevTools()
    } else {
      mainWindow.webContents.openDevTools({ mode: 'right' })
    }
  })

  ipcMain.on('is-fullscreen', (event) => {
    event.returnValue = mainWindow?.isFullScreen() ?? false
  })

  if (!EXTERNAL_DJANGO) {
    freePort(DJANGO_PORT)
    let portFree = false
    for (let i = 0; i < 10; i++) {
      portFree = await isPortFree(DJANGO_PORT)
      if (portFree) break
      await new Promise(r => setTimeout(r, 300))
    }
    startDjango()
  }

  // Start the search worker server BEFORE creating the main window
  startWorkerServer()
  createSearchWorker()

  await createWindow()

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      if (!djangoProcess && !EXTERNAL_DJANGO) {
        safeLog('[Firecat] Restarting Django...')
        startDjango()
      }
      await createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (!EXTERNAL_DJANGO) {
      killDjango()
      freePort(DJANGO_PORT)
    }
    app.quit()
  }
})

app.on('before-quit', () => {
  if (!EXTERNAL_DJANGO) {
    killDjango()
    freePort(DJANGO_PORT)
  }
})