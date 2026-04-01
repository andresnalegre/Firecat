import { useState, useCallback, useRef } from 'react'
import { historyService } from '../services/history'

export const MAX_TABS = 15

const isElectron = Boolean(window.firecat)
const genId      = () => Math.random().toString(36).slice(2, 9)

const isUrl = (s) => {
  const t = s.trim()
  if (/^https?:\/\//i.test(t)) return true
  if (/^firecat:\/\//i.test(t)) return true
  if (/^www\./i.test(t)) return true
  if (/^[^\s]+\.[a-z]{2,}(\/.*)?$/i.test(t) && !t.includes(' ')) return true
  return false
}

const PROXY = '/api/proxy/?url='

const stripWww = (s) => s
  .replace(/^(https?:\/\/)www\./i, '$1')
  .replace(/^www\./i, '')

const normaliseUrl = (u) => u
  .replace(/^https?:\/\/www\./i, 'https://')
  .replace(/\/$/, '')
  .toLowerCase()

const toUrl = (s, hacker = false) => {
  const trimmed = s.trim()

  if (/^firecat:\/\//i.test(trimmed)) return trimmed

  if (/^https?:\/\//i.test(trimmed)) {
    const clean = stripWww(trimmed)
    if (hacker) return clean
    return isElectron ? clean : `${PROXY}${encodeURIComponent(clean)}`
  }

  if (isUrl(trimmed)) {
    const clean = `https://${stripWww(trimmed)}`
    if (hacker) return clean
    return isElectron ? clean : `${PROXY}${encodeURIComponent(clean)}`
  }

  if (hacker) return `firecat://search?q=${encodeURIComponent(trimmed)}`

  const searchUrl = isElectron
    ? `https://www.google.com/search?q=${encodeURIComponent(trimmed)}&hl=en`
    : `https://www.bing.com/search?q=${encodeURIComponent(trimmed)}&setlang=en&cc=US&ensearch=1`

  return isElectron ? searchUrl : `${PROXY}${encodeURIComponent(searchUrl)}`
}

const toHistoryUrl = (s) => {
  if (/^firecat:\/\//i.test(s)) return s
  if (/^https?:\/\//i.test(s)) return stripWww(s).replace(/\/$/, '')
  if (isUrl(s)) return `https://${stripWww(s)}`.replace(/\/$/, '')
  return `https://www.google.com/search?q=${encodeURIComponent(s)}`
}

export const cleanUrl = (url) => {
  if (!url) return ''
  try {
    if (url.includes('/api/proxy/?url=')) {
      return decodeURIComponent(url.split('/api/proxy/?url=')[1])
    }
  } catch {}
  return url
}

export const toProxyUrl = (url) => `${PROXY}${encodeURIComponent(url)}`

const makeTab = (overrides = {}) => ({
  id:       genId(),
  title:    'Firecat',
  url:      '',
  isHome:   true,
  favicon:  '🔥',
  hist:     [],
  histIdx:  -1,
  useProxy: false,
  ...overrides,
})

export function useBrowser() {
  const [tabs, setTabs]        = useState([makeTab()])
  const [activeTab, setActive] = useState(0)
  const localHistory           = useRef([])

  const currentTab = tabs[activeTab] ?? tabs[0]

  const _push = (tab, url, title, hacker, useProxy = false) => {
    const hist = [...(tab.hist || []).slice(0, (tab.histIdx ?? -1) + 1), url]
    return {
      ...tab,
      url,
      title,
      isHome:   false,
      favicon:  hacker ? '⚡' : '🌐',
      hist,
      histIdx:  hist.length - 1,
      useProxy,
    }
  }

  const navigate = useCallback((query, hacker = false, tabIdx = null) => {
    const idx   = tabIdx ?? activeTab
    const url   = toUrl(query, hacker)
    const title = isUrl(query)
      ? query.startsWith('firecat://')
        ? query.replace('firecat://', '').replace('/', '').replace(/^\w/, c => c.toUpperCase())
        : stripWww(query).replace(/^https?:\/\//, '').split('/')[0]
      : `Search: ${query}`

    setTabs(prev => {
      const updated = [...prev]

      if (idx === 0 && prev[0].isHome) {
        if (prev.length >= MAX_TABS) return prev
        const t = _push(makeTab({ title: 'New Tab' }), url, title, hacker)
        setTimeout(() => setActive(prev.length), 0)
        return [...prev, t]
      }

      updated[idx] = _push({ ...updated[idx] }, url, title, hacker)
      return updated
    })

    if (!/^firecat:\/\//i.test(url)) {
      const hUrl = toHistoryUrl(query)
      localHistory.current = [
        { url: hUrl, title },
        ...localHistory.current.filter(h => normaliseUrl(h.url) !== normaliseUrl(hUrl)),
      ].slice(0, 1000)
      historyService.add({ url: hUrl, title }).catch(() => {})
    }
  }, [activeTab])

  const fallbackToProxy = useCallback((tabIdx) => {
    setTabs(prev => {
      const updated = [...prev]
      const tab     = updated[tabIdx]
      if (!tab || !tab.url || tab.useProxy) return prev
      const proxyUrl = toProxyUrl(tab.url)
      updated[tabIdx] = { ...tab, url: proxyUrl, useProxy: true }
      return updated
    })
  }, [])

  const goBack = useCallback(() => {
    setTabs(prev => {
      const tab = prev[activeTab]
      if (!tab || tab.histIdx <= 0) return prev
      const updated = [...prev]
      const newIdx  = tab.histIdx - 1
      updated[activeTab] = { ...tab, histIdx: newIdx, url: tab.hist[newIdx], useProxy: false }
      return updated
    })
  }, [activeTab])

  const goForward = useCallback(() => {
    setTabs(prev => {
      const tab = prev[activeTab]
      if (!tab || tab.histIdx >= (tab.hist?.length ?? 0) - 1) return prev
      const updated = [...prev]
      const newIdx  = tab.histIdx + 1
      updated[activeTab] = { ...tab, histIdx: newIdx, url: tab.hist[newIdx], useProxy: false }
      return updated
    })
  }, [activeTab])

  const reload = useCallback(() => {
    setTabs(prev => {
      const updated  = [...prev]
      const tab      = updated[activeTab]
      const savedUrl = tab.url
      updated[activeTab] = { ...tab, url: '' }
      setTimeout(() => {
        setTabs(p => {
          const u = [...p]
          u[activeTab] = { ...u[activeTab], url: savedUrl }
          return u
        })
      }, 50)
      return updated
    })
  }, [activeTab])

  const goHome = useCallback(() => {
    setTabs(prev => prev.map((t, i) =>
      i === activeTab
        ? { ...t, url: '', title: i === 0 ? 'Firecat' : 'New Tab', isHome: true, favicon: '🔥', useProxy: false }
        : t
    ))
  }, [activeTab])

  const addTab = useCallback(() => {
    if (tabs.length >= MAX_TABS) return
    setTabs(prev => [...prev, makeTab({ title: 'New Tab' })])
    setActive(tabs.length)
  }, [tabs.length])

  const closeTab = useCallback((idx) => {
    if (idx === 0 || tabs.length === 1) return
    setTabs(prev => prev.filter((_, i) => i !== idx))
    setActive(prev => Math.min(prev, tabs.length - 2))
  }, [tabs.length])

  const switchTab = useCallback((idx) => setActive(idx), [])

  const canGoBack    = (currentTab?.histIdx ?? 0) > 0
  const canGoForward = (currentTab?.histIdx ?? 0) < ((currentTab?.hist?.length ?? 1) - 1)

  return {
    tabs, activeTab, currentTab,
    navigate, goBack, goForward, reload, goHome,
    addTab, closeTab, switchTab,
    canGoBack, canGoForward, fallbackToProxy,
    localHistory: localHistory.current, MAX_TABS,
  }
}