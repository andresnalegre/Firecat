import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../context/ThemeContext'
import { historyService } from '../services/history'
import DownloadsPage from './DownloadsPage'

const isElectron    = Boolean(window.firecat)
const isSearchProxy = (url) => url?.startsWith('firecat://search')
const isFirecatPage = (url) => url?.startsWith('firecat://') && !url?.startsWith('firecat://search')

const getQuery = (url) => {
  try { return decodeURIComponent(url.split('?q=')[1] || '') }
  catch { return '' }
}

function DeepResults({ url, onNavigate }) {
  const { theme } = useTheme()
  const [groups,  setGroups]  = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [hovered, setHovered] = useState(null)
  const query = getQuery(url)

  useEffect(() => {
    setLoading(true); setError(null); setGroups([])
    const q = url.split('?q=')[1] || ''
    fetch(`/api/search/?q=${q}`)
      .then(r => r.json())
      .then(data => {
        if (data.groups?.length > 0) setGroups(data.groups)
        else setError(data.error || 'No results found')
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [url])

  const bg      = theme.mode === 'dark' ? '#111113' : '#f5f5f7'
  const card    = theme.mode === 'dark' ? 'rgba(255,255,255,0.04)' : '#fff'
  const cardHov = theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : '#f0f0f5'
  const muted   = theme.textMuted
  const accent  = theme.accent
  const border  = theme.border

  return (
    <div style={{
      width: '100%', height: '100%', overflowY: 'auto',
      background: bg, fontFamily: "'Segoe UI', sans-serif",
      position: 'relative',
    }}>
      <style>{`
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin   { to{transform:rotate(360deg)} }
        ::-webkit-scrollbar { width: 6px }
        ::-webkit-scrollbar-track { background: transparent }
        ::-webkit-scrollbar-thumb { background: ${border}; border-radius: 3px }
      `}</style>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '36px 24px 80px' }}>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          marginBottom: 32,
          paddingBottom: 20,
          borderBottom: `1px solid ${border}`,
          textAlign: 'center',
        }}>
          <img src="/Firecat.png" alt="Firecat" draggable="false"
            style={{ width: 120, height: 120, objectFit: 'contain', marginBottom: 8, pointerEvents: 'none' }} />
          <div style={{ fontSize: 14, color: muted, marginTop: 6 }}>
            {loading ? '' : `Results for "${query}"`}
          </div>
        </div>

        {!loading && !error && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 36 }}>
            {groups.map((group, gi) => (
              <div key={group.id} style={{
                animationName: 'fadeUp', animationDuration: '0.4s',
                animationFillMode: 'both', animationDelay: `${gi * 0.06}s`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                  <div style={{ height: 1, flex: 1, background: border }} />
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: accent,
                    letterSpacing: 0.8, textTransform: 'uppercase',
                    background: `${accent}15`, borderRadius: 20,
                    padding: '3px 12px', border: `1px solid ${accent}33`,
                    flexShrink: 0,
                  }}>
                    {group.label}
                  </span>
                  <span style={{ fontSize: 10, color: muted, flexShrink: 0 }}>
                    {group.items.length} results
                  </span>
                  <div style={{ height: 1, flex: 1, background: border }} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {group.items.map((item, i) => {
                    const key   = `${group.id}-${i}`
                    const isHov = hovered === key
                    return (
                      <div
                        key={key}
                        onClick={() => onNavigate(item.link)}
                        onMouseEnter={() => setHovered(key)}
                        onMouseLeave={() => setHovered(null)}
                        style={{
                          padding: '14px 18px', borderRadius: 12,
                          border: `1px solid ${isHov ? accent + '55' : border}`,
                          background: isHov ? cardHov : card,
                          cursor: 'pointer', transition: 'all 0.15s',
                          boxShadow: isHov
                            ? `0 4px 20px ${accent}18`
                            : theme.mode === 'dark' ? 'none' : '0 1px 4px rgba(0,0,0,0.05)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
                          <img
                            src={`https://www.google.com/s2/favicons?domain=${item.displayLink}&sz=16`}
                            alt="" width={13} height={13}
                            style={{ borderRadius: 3, flexShrink: 0 }}
                            onError={e => e.target.style.display = 'none'}
                          />
                          <span style={{
                            fontSize: 11, color: muted,
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
                          }}>
                            {item.displayLink}
                          </span>
                          {isHov && (
                            <span style={{ fontSize: 11, color: accent, fontWeight: 600, flexShrink: 0 }}>
                              Open →
                            </span>
                          )}
                        </div>
                        <div style={{
                          fontSize: 14, fontWeight: 600, lineHeight: 1.4,
                          color: isHov ? accent : theme.text,
                          marginBottom: 4, transition: 'color 0.15s',
                        }}>
                          {item.title}
                        </div>
                        {item.snippet && (
                          <div style={{
                            fontSize: 12, color: muted, lineHeight: 1.6,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}>
                            {item.snippet}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}

            <div style={{
              textAlign: 'center', marginTop: 20,
              fontSize: 12, color: muted, opacity: 0.5,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}>
              <img src="/Firecat.png" alt="" width={14} height={14}
                style={{ opacity: 0.4, pointerEvents: 'none' }} />
              Firecat Deep Search · Google Hacking Operators
            </div>
          </div>
        )}

        {error && !loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div style={{ fontSize: 40 }}>🔍</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: theme.text }}>No results found</div>
            <div style={{ fontSize: 13, color: muted }}>{error}</div>
          </div>
        )}
      </div>

      {loading && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          gap: 16,
        }}>
          <div style={{
            width: 50, height: 50,
            border: `4px solid ${border}`,
            borderTop: `4px solid ${accent}`,
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }} />
          <div style={{ fontSize: 14, color: muted }}>Deep Search in process...</div>
        </div>
      )}
    </div>
  )
}

function debounce(fn, ms) {
  let t
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms) }
}

function WebviewPool({ tabs, activeTab, isHomeActive, onNavigate, onAudioChange, onFallbackToProxy }) {
  const webviewRefs = useRef({})
  const lastUrls    = useRef({})

  const recordHistory = useRef(
    debounce((url) => {
      if (!url || url.startsWith('about:') || url.startsWith('devtools:') || url.startsWith('firecat://')) return
      const title = url.replace(/^https?:\/\//, '').split('/')[0]
      historyService.add({ url, title }).catch(() => {})
    }, 800)
  ).current

  useEffect(() => {
    const wvs      = webviewRefs.current
    const handlers = {}

    Object.entries(wvs).forEach(([id, wv]) => {
      if (!wv) return
      const onAudio  = () => onAudioChange(id, true)
      const onSilent = () => onAudioChange(id, false)
      const onNav    = (e) => {
        if (!e.url || e.url.startsWith('about:') || e.url.startsWith('devtools:')) return
        if (lastUrls.current[id] === e.url) return
        lastUrls.current[id] = e.url
        recordHistory(e.url)
      }
      const onFail = (e) => {
        const sslErrors = [-113, -200, -201, -202, -203, -324]
        if (sslErrors.includes(e.errorCode)) {
          const tabIdx = tabs.findIndex(t => t.id === id)
          if (tabIdx !== -1) onFallbackToProxy(tabIdx)
        }
      }
      handlers[id] = { onAudio, onSilent, onNav, onFail }
      wv.addEventListener('media-started-playing', onAudio)
      wv.addEventListener('media-paused',          onSilent)
      wv.addEventListener('did-navigate',          onNav)
      wv.addEventListener('did-navigate-in-page',  onNav)
      wv.addEventListener('did-fail-load',         onFail)
    })

    return () => {
      Object.entries(wvs).forEach(([id, wv]) => {
        if (!wv || !handlers[id]) return
        wv.removeEventListener('media-started-playing', handlers[id].onAudio)
        wv.removeEventListener('media-paused',          handlers[id].onSilent)
        wv.removeEventListener('did-navigate',          handlers[id].onNav)
        wv.removeEventListener('did-navigate-in-page',  handlers[id].onNav)
        wv.removeEventListener('did-fail-load',         handlers[id].onFail)
      })
    }
  }, [tabs, onAudioChange, recordHistory, onFallbackToProxy])

  return (
    <div style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      {tabs.map((tab, i) => {
        if (!tab.url) return null
        const isActive = i === activeTab && !isHomeActive

        if (isSearchProxy(tab.url)) {
          return (
            <div key={tab.id} style={{ position: 'absolute', inset: 0, display: isActive ? 'flex' : 'none' }}>
              <DeepResults url={tab.url} onNavigate={onNavigate} />
            </div>
          )
        }

        if (isFirecatPage(tab.url)) {
          return (
            <div key={tab.id} style={{ position: 'absolute', inset: 0, display: isActive ? 'flex' : 'none', overflow: 'auto' }}>
              {tab.url === 'firecat://downloads' && <DownloadsPage />}
            </div>
          )
        }

        return (
          <webview
            key={tab.id}
            ref={el => { if (el) webviewRefs.current[tab.id] = el }}
            src={tab.url}
            style={{
              position: 'absolute', inset: 0,
              width: '100%', height: '100%',
              border: 'none',
              display: isActive ? 'flex' : 'none',
            }}
            allowpopups="true"
            disablewebsecurity="true"
            partition="persist:firecat"
            useragent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
          />
        )
      })}
    </div>
  )
}

export default function BrowserPage({ tabs, activeTab, tab, onGoHome, onNavigate, onAudioChange, onFallbackToProxy }) {
  const { theme } = useTheme()
  const isHomeActive = tab?.isHome ?? true

  if (isElectron) {
    return (
      <div style={{ position: 'absolute', inset: 0, background: theme.bg }}>
        <WebviewPool
          tabs={tabs}
          activeTab={activeTab}
          isHomeActive={isHomeActive}
          onNavigate={onNavigate}
          onAudioChange={onAudioChange ?? (() => {})}
          onFallbackToProxy={onFallbackToProxy ?? (() => {})}
        />
      </div>
    )
  }

  if (isHomeActive) return null

  if (isSearchProxy(tab.url)) {
    return <DeepResults url={tab.url} onNavigate={onNavigate} />
  }

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: theme.bg }}>
      <iframe
        key={tab.url}
        src={tab.url}
        title={tab.title}
        style={{ flex: 1, border: 'none', width: '100%', height: '100%' }}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
        allowFullScreen
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads"
      />
    </div>
  )
}