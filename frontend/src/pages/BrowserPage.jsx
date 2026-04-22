import { useState, useEffect, useRef, useCallback } from 'react'
import { useTheme } from '../context/ThemeContext'
import { historyService } from '../services/history'
import DownloadsPage from './DownloadsPage'

const isElectron    = Boolean(window.firecat)
const isSearchProxy = (url) => url?.startsWith('firecat://search')
const isFirecatPage = (url) => url?.startsWith('firecat://') && !url?.startsWith('firecat://search')

const getQuery = (url) => {
  try { return decodeURIComponent(url.split('?q=')[1]?.split('&')[0] || '') }
  catch { return '' }
}

// ---------------------------------------------------------------------------
// Category filter bar
// ---------------------------------------------------------------------------
const CATEGORIES = [
  { id: 'all',     label: 'All'     },
  { id: 'people',  label: 'People'  },
  { id: 'contact', label: 'Contact' },
  { id: 'files',   label: 'Files'   },
  { id: 'web',     label: 'Web'     },
]

function CategoryBar({ active, onChange, theme }) {
  return (
    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 24 }}>
      {CATEGORIES.map((cat) => {
        const isActive = active === cat.id
        return (
          <button
            key={cat.id}
            onClick={() => onChange(cat.id)}
            style={{
              padding: '5px 14px', borderRadius: 6,
              border: `1px solid ${isActive ? theme.accent + '60' : theme.border}`,
              background: isActive ? `${theme.accent}15` : 'transparent',
              color: isActive ? theme.accent : theme.textMuted,
              fontSize: 12, fontWeight: isActive ? 600 : 400,
              cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
            }}
          >
            {cat.label}
          </button>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Inspect panel — shown when user clicks "Inspect" on a result
// ---------------------------------------------------------------------------
function InspectPanel({ url, theme, onClose }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [tab,     setTab]     = useState('emails')
  const isDark  = theme.mode === 'dark'
  const muted   = theme.textMuted
  const border  = theme.border
  const accent  = theme.accent

  useEffect(() => {
    setLoading(true); setError(null); setData(null)
    fetch(`/api/search/inspect/?url=${encodeURIComponent(url)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [url])

  const TABS = [
    { id: 'emails',   label: 'Emails',     count: data?.summary?.emails },
    { id: 'phones',   label: 'Phones',     count: data?.summary?.phones },
    { id: 'socials',  label: 'Socials',    count: data?.summary?.socials },
    { id: 'meta',     label: 'Meta',       count: data?.meta ? Object.keys(data.meta).length : 0 },
    { id: 'comments', label: 'Comments',   count: data?.summary?.comments },
    { id: 'links',    label: 'Links',      count: data?.summary?.ext_links },
    { id: 'tech',     label: 'Tech',       count: data?.tech?.length },
    { id: 'secrets',  label: 'Secrets',    count: (data?.summary?.exposed_keys || 0) + (data?.summary?.crypto || 0) },
  ]

  const renderContent = () => {
    if (!data) return null
    const itemStyle = {
      padding: '8px 10px', borderRadius: 7, marginBottom: 4,
      background: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
      border: `1px solid ${border}`, fontSize: 12,
      wordBreak: 'break-all', color: theme.text,
    }
    const empty = (
      <div style={{ padding: '24px 0', textAlign: 'center', color: muted, fontSize: 12, opacity: 0.5 }}>
        Nothing found
      </div>
    )

    if (tab === 'emails') {
      if (!data.emails?.length) return empty
      return data.emails.map((e, i) => (
        <div key={i} style={itemStyle}>
          <a href={`mailto:${e}`} style={{ color: accent, textDecoration: 'none' }}>{e}</a>
        </div>
      ))
    }
    if (tab === 'phones') {
      if (!data.phones?.length) return empty
      return data.phones.map((p, i) => <div key={i} style={itemStyle}>{p}</div>)
    }
    if (tab === 'socials') {
      if (!data.socials?.length) return empty
      return data.socials.map((s, i) => (
        <div key={i} style={itemStyle}>
          <a href={s} target="_blank" rel="noreferrer" style={{ color: accent, textDecoration: 'none' }}>{s}</a>
        </div>
      ))
    }
    if (tab === 'meta') {
      const entries = Object.entries(data.meta || {})
      if (!entries.length) return empty
      return entries.map(([k, v], i) => (
        <div key={i} style={{ ...itemStyle, display: 'flex', gap: 8 }}>
          <span style={{ color: muted, flexShrink: 0, minWidth: 120, fontSize: 11 }}>{k}</span>
          <span style={{ color: theme.text }}>{v}</span>
        </div>
      ))
    }
    if (tab === 'comments') {
      if (!data.comments?.length) return empty
      return data.comments.map((c, i) => (
        <div key={i} style={{ ...itemStyle, fontFamily: 'monospace', fontSize: 11, color: muted }}>{c}</div>
      ))
    }
    if (tab === 'links') {
      if (!data.ext_links?.length) return empty
      return data.ext_links.map((l, i) => (
        <div key={i} style={itemStyle}>
          <div style={{ color: muted, fontSize: 10, marginBottom: 2 }}>{l.domain}</div>
          <a href={l.url} target="_blank" rel="noreferrer" style={{ color: accent, textDecoration: 'none', fontSize: 11 }}>
            {l.text || l.url}
          </a>
        </div>
      ))
    }
    if (tab === 'tech') {
      if (!data.tech?.length) return empty
      return data.tech.map((t, i) => <div key={i} style={itemStyle}>{t}</div>)
    }
    if (tab === 'secrets') {
      const items = [
        ...(data.exposed_keys || []).map(k => ({ type: 'API Key', val: k })),
        ...(data.crypto       || []).map(k => ({ type: 'Crypto',  val: k })),
        ...(data.ips          || []).map(k => ({ type: 'IP',      val: k })),
      ]
      if (!items.length) return empty
      return items.map((item, i) => (
        <div key={i} style={itemStyle}>
          <span style={{ color: accent, fontSize: 10, marginRight: 8, fontWeight: 600 }}>{item.type}</span>
          <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{item.val}</span>
        </div>
      ))
    }
    return null
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 500,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: 560, maxHeight: '80vh',
          background: isDark ? '#1c1c1e' : '#fff',
          border: `1px solid ${border}`,
          borderRadius: 16, boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '16px 18px 12px',
          borderBottom: `1px solid ${border}`,
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
        }}>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: theme.text, marginBottom: 3 }}>
              Deep Inspect
            </div>
            <div style={{ fontSize: 11, color: muted, opacity: 0.6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {url}
            </div>
            {data?.title && (
              <div style={{ fontSize: 12, color: muted, marginTop: 4, opacity: 0.7 }}>
                {data.title}
              </div>
            )}
          </div>
          <button onClick={onClose} style={{
            width: 26, height: 26, borderRadius: '50%', border: 'none', flexShrink: 0,
            background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
            color: muted, fontSize: 14, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>×</button>
        </div>

        {loading && (
          <div style={{ padding: '48px 0', textAlign: 'center', color: muted }}>
            <div style={{
              width: 32, height: 32, margin: '0 auto 12px',
              border: `3px solid ${border}`, borderTop: `3px solid ${accent}`,
              borderRadius: '50%', animation: 'spin 0.8s linear infinite',
            }} />
            <div style={{ fontSize: 12 }}>Extracting data...</div>
          </div>
        )}

        {error && !loading && (
          <div style={{ padding: '32px 18px', textAlign: 'center', color: muted, fontSize: 13 }}>
            Could not fetch page: {error}
          </div>
        )}

        {data && !loading && (
          <>
            {/* Tab bar */}
            <div style={{
              display: 'flex', gap: 2, padding: '10px 14px 0',
              borderBottom: `1px solid ${border}`,
              overflowX: 'auto', flexShrink: 0,
            }}>
              {TABS.map(t => {
                const isActive = tab === t.id
                const hasData  = t.count > 0
                return (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    style={{
                      padding: '5px 10px 8px', borderRadius: '6px 6px 0 0',
                      border: 'none', background: 'transparent',
                      color: isActive ? accent : (hasData ? theme.text : muted),
                      fontSize: 11, fontWeight: isActive ? 600 : 400,
                      cursor: 'pointer', flexShrink: 0, fontFamily: 'inherit',
                      borderBottom: isActive ? `2px solid ${accent}` : '2px solid transparent',
                      opacity: hasData ? 1 : 0.4,
                    }}
                  >
                    {t.label}
                    {t.count > 0 && (
                      <span style={{
                        marginLeft: 4, fontSize: 10,
                        background: isActive ? `${accent}30` : (isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.07)'),
                        color: isActive ? accent : muted,
                        borderRadius: 4, padding: '1px 5px',
                      }}>
                        {t.count}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px 16px' }}>
              {renderContent()}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Result card
// ---------------------------------------------------------------------------
function ResultCard({ item, onNavigate, onInspect, theme, accent, border, muted }) {
  const [hovered, setHovered] = useState(false)
  const isDark  = theme.mode === 'dark'
  const cardBg  = isDark ? 'rgba(255,255,255,0.04)' : '#fff'
  const cardHov = isDark ? 'rgba(255,255,255,0.07)' : '#f0f0f5'

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '12px 16px', borderRadius: 10,
        border: `1px solid ${hovered ? accent + '44' : border}`,
        background: hovered ? cardHov : cardBg,
        transition: 'all 0.15s',
        boxShadow: hovered ? `0 3px 16px ${accent}14` : (isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.04)'),
      }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
        <img
          src={`https://www.google.com/s2/favicons?domain=${item.displayLink}&sz=16`}
          alt="" width={13} height={13}
          style={{ borderRadius: 3, flexShrink: 0 }}
          onError={e => { e.target.style.display = 'none' }}
        />
        <span style={{ fontSize: 11, color: muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
          {item.displayLink}
        </span>
        {item.source && (
          <span style={{ fontSize: 9, color: muted, opacity: 0.4, textTransform: 'uppercase', letterSpacing: 0.5, flexShrink: 0 }}>
            {item.source}
          </span>
        )}
      </div>

      {/* Title */}
      <div
        onClick={() => onNavigate(item.link)}
        style={{
          fontSize: 13, fontWeight: 600, lineHeight: 1.4,
          color: hovered ? accent : theme.text,
          marginBottom: 4, transition: 'color 0.15s',
          cursor: 'pointer',
        }}
      >
        {item.title}
      </div>

      {/* Snippet */}
      {item.snippet && (
        <div style={{
          fontSize: 12, color: muted, lineHeight: 1.6,
          display: '-webkit-box', WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical', overflow: 'hidden',
          marginBottom: 8,
        }}>
          {item.snippet}
        </div>
      )}

      {/* Actions */}
      <div style={{
        display: 'flex', gap: 6, marginTop: 4,
        opacity: hovered ? 1 : 0, transition: 'opacity 0.15s',
      }}>
        <button
          onClick={() => onNavigate(item.link)}
          style={{
            padding: '3px 10px', borderRadius: 5, border: `1px solid ${border}`,
            background: 'transparent', color: muted, fontSize: 11,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >
          Open
        </button>
        <button
          onClick={() => onInspect(item.link)}
          style={{
            padding: '3px 10px', borderRadius: 5,
            border: `1px solid ${accent}40`,
            background: `${accent}12`, color: accent, fontSize: 11,
            cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500,
          }}
        >
          Inspect
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Group section
// ---------------------------------------------------------------------------
function GroupSection({ group, onNavigate, onInspect, theme, accent, border, muted, isNew }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div style={{ animation: isNew ? 'fadeUp 0.35s both' : 'none' }}>
      <div
        onClick={() => setCollapsed(p => !p)}
        style={{
          display: 'flex', alignItems: 'center', gap: 10,
          marginBottom: collapsed ? 0 : 12, cursor: 'pointer', userSelect: 'none',
        }}
      >
        <div style={{ height: 1, flex: 1, background: border }} />
        <span style={{
          fontSize: 10, fontWeight: 700, color: accent,
          letterSpacing: 0.8, textTransform: 'uppercase',
          background: `${accent}12`, borderRadius: 20,
          padding: '3px 11px', border: `1px solid ${accent}25`, flexShrink: 0,
        }}>
          {group.label}
        </span>
        <span style={{ fontSize: 10, color: muted, opacity: 0.5, flexShrink: 0 }}>
          {group.items.length}
        </span>
        <span style={{ fontSize: 9, color: muted, opacity: 0.35, flexShrink: 0 }}>
          {collapsed ? '▶' : '▼'}
        </span>
        <div style={{ height: 1, flex: 1, background: border }} />
      </div>

      {!collapsed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {group.items.map((item, i) => (
            <ResultCard
              key={`${group.id}-${i}`}
              item={item}
              onNavigate={onNavigate}
              onInspect={onInspect}
              theme={theme}
              accent={accent}
              border={border}
              muted={muted}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Deep Search results — SSE streaming
// ---------------------------------------------------------------------------
function DeepResults({ url, onNavigate }) {
  const { theme }  = useTheme()
  const [groups,     setGroups]     = useState([])
  const [newIds,     setNewIds]     = useState(new Set())
  const [loading,    setLoading]    = useState(true)
  const [done,       setDone]       = useState(false)
  const [error,      setError]      = useState(null)
  const [cached,     setCached]     = useState(false)
  const [activeGroup, setActiveGroup] = useState(null)
  const [inspectUrl,  setInspectUrl]  = useState(null)
  const esRef = useRef(null)

  const query = getQuery(url)

  const startSearch = useCallback(() => {
    if (esRef.current) esRef.current.close()
    setGroups([])
    setNewIds(new Set())
    setLoading(true)
    setDone(false)
    setError(null)
    setCached(false)
    setActiveGroup(null)

    const urlParams = new URLSearchParams(url.includes('?') ? url.split('?')[1] : '')
    const qValue    = urlParams.get('q') || ''
    const baseCats  = urlParams.get('categories') || 'all'
    const catParam  = (baseCats && baseCats !== 'all') ? `&categories=${baseCats}` : ''
    const esUrl     = `/api/search/?q=${encodeURIComponent(qValue)}${catParam}`

    const es = new EventSource(esUrl)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'group') {
          const g = msg.group
          setGroups(prev => {
            if (prev.find(x => x.id === g.id)) return prev
            const next = [...prev, g]
            if (!activeGroup) setActiveGroup(g.id)
            return next
          })
          setNewIds(prev => new Set([...prev, g.id]))
          setLoading(false)
        }
        if (msg.type === 'done') {
          setDone(true); setLoading(false); setCached(msg.cached ?? false)
          es.close()
        }
        if (msg.type === 'error') {
          setError(msg.message); setLoading(false); setDone(true)
          es.close()
        }
      } catch {}
    }

    es.onerror = () => {
      setLoading(false); setDone(true)
      if (groups.length === 0) setError('Search failed. Try again.')
      es.close()
    }
  }, [url])

  useEffect(() => {
    startSearch()
    return () => esRef.current?.close()
  }, [url])

  // Set first group as active when groups arrive
  useEffect(() => {
    if (groups.length > 0 && !activeGroup) {
      setActiveGroup(groups[0].id)
    }
  }, [groups])

  const muted  = theme.textMuted
  const accent = theme.accent
  const border = theme.border
  const isDark = theme.mode === 'dark'
  const bg     = isDark ? '#111113' : '#f5f5f7'

  const currentGroup = groups.find(g => g.id === activeGroup)
  const totalResults = groups.reduce((s, g) => s + g.items.length, 0)

  // Loading state — só spinner
  if (loading && groups.length === 0) {
    return (
      <div style={{
        width: '100%', height: '100%', background: bg,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 18,
      }}>
        <style>{`
          @keyframes spin  { to{transform:rotate(360deg)} }
          @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.2} }
        `}</style>
        <div style={{
          width: 44, height: 44,
          border: `3px solid ${border}`,
          borderTop: `3px solid ${accent}`,
          borderRadius: '50%', animation: 'spin 0.8s linear infinite',
        }} />
        <div style={{ fontSize: 13, color: accent, animation: 'pulse 1.4s ease-in-out infinite', letterSpacing: '0.04em' }}>
          Scanning...
        </div>
      </div>
    )
  }

  // Error state
  if (error && done && groups.length === 0) {
    return (
      <div style={{
        width: '100%', height: '100%', background: bg,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 10,
      }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: theme.text }}>No results found</div>
        <div style={{ fontSize: 12, color: muted }}>{error}</div>
        <button onClick={startSearch} style={{
          marginTop: 6, padding: '7px 18px', borderRadius: 7,
          border: `1px solid ${accent}50`, background: `${accent}12`,
          color: accent, fontSize: 12, cursor: 'pointer', fontFamily: 'inherit',
        }}>Try again</button>
      </div>
    )
  }

  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', background: bg,
      fontFamily: "'Syne', 'Segoe UI', sans-serif",
      overflow: 'hidden',
    }}>
      <style>{`
        @keyframes fadeUp { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin   { to{transform:rotate(360deg)} }
        ::-webkit-scrollbar { width: 4px }
        ::-webkit-scrollbar-track { background: transparent }
        ::-webkit-scrollbar-thumb { background: ${border}; border-radius: 3px }
      `}</style>

      {inspectUrl && (
        <InspectPanel url={inspectUrl} theme={theme} onClose={() => setInspectUrl(null)} />
      )}

      {/* Sidebar — group filters */}
      <div style={{
        width: 220, flexShrink: 0,
        borderRight: `1px solid ${border}`,
        display: 'flex', flexDirection: 'column',
        overflowY: 'auto', overflowX: 'hidden',
        background: isDark ? '#0e0e10' : '#f0f0f2',
      }}>
        {/* Header info */}
        <div style={{ padding: '16px 14px 12px', borderBottom: `1px solid ${border}` }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: theme.text, marginBottom: 2 }}>
            {query}
          </div>
          <div style={{ fontSize: 10, color: muted, opacity: 0.6 }}>
            {done
              ? `${groups.length} groups · ${totalResults} results`
              : <span style={{ color: accent }}>Scanning...</span>
            }
          </div>
        </div>

        {/* Group list */}
        <div style={{ flex: 1, padding: '8px 0' }}>
          {groups.map(g => {
            const isActive = g.id === activeGroup
            return (
              <div
                key={g.id}
                onClick={() => setActiveGroup(g.id)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '8px 14px', cursor: 'pointer',
                  background: isActive
                    ? (isDark ? `${accent}18` : `${accent}12`)
                    : 'transparent',
                  borderLeft: `2px solid ${isActive ? accent : 'transparent'}`,
                  transition: 'all 0.12s',
                }}
                onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)' }}
                onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
              >
                <span style={{
                  fontSize: 12, color: isActive ? accent : muted,
                  fontWeight: isActive ? 600 : 400,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  flex: 1,
                }}>
                  {g.label}
                </span>
                <span style={{
                  fontSize: 10, color: isActive ? accent : muted,
                  opacity: isActive ? 0.8 : 0.4,
                  marginLeft: 6, flexShrink: 0,
                  background: isActive ? `${accent}20` : (isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'),
                  borderRadius: 4, padding: '1px 5px',
                }}>
                  {g.items.length}
                </span>
              </div>
            )
          })}

          {/* Loading indicator in sidebar */}
          {loading && (
            <div style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 7 }}>
              <div style={{
                width: 12, height: 12, flexShrink: 0,
                border: `2px solid ${border}`, borderTop: `2px solid ${accent}`,
                borderRadius: '50%', animation: 'spin 0.8s linear infinite',
              }} />
              <span style={{ fontSize: 11, color: muted, opacity: 0.5 }}>Loading...</span>
            </div>
          )}
        </div>

        {/* Footer */}
        {done && (
          <div style={{
            padding: '10px 14px', borderTop: `1px solid ${border}`,
            fontSize: 10, color: muted, opacity: 0.35, textAlign: 'center',
          }}>
            {cached ? 'cached' : 'live'} · OSINT
          </div>
        )}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px 60px' }}>
        {currentGroup ? (
          <div>
            {/* Group title */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
              paddingBottom: 12, borderBottom: `1px solid ${border}`,
            }}>
              <span style={{
                fontSize: 11, fontWeight: 700, color: accent,
                letterSpacing: 0.8, textTransform: 'uppercase',
                background: `${accent}12`, borderRadius: 20,
                padding: '3px 11px', border: `1px solid ${accent}25`,
              }}>
                {currentGroup.label}
              </span>
              <span style={{ fontSize: 11, color: muted, opacity: 0.5 }}>
                {currentGroup.items.length} results
              </span>
            </div>

            {/* Results */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {currentGroup.items.map((item, i) => (
                <ResultCard
                  key={`${currentGroup.id}-${i}`}
                  item={item}
                  onNavigate={onNavigate}
                  onInspect={setInspectUrl}
                  theme={theme}
                  accent={accent}
                  border={border}
                  muted={muted}
                />
              ))}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60%' }}>
            <div style={{ fontSize: 13, color: muted, opacity: 0.4 }}>Select a group</div>
          </div>
        )}
      </div>
    </div>
  )
}


// ---------------------------------------------------------------------------
// Webview pool (Electron)
// ---------------------------------------------------------------------------
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
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 'none', display: isActive ? 'flex' : 'none' }}
            allowpopups="true"
            disablewebsecurity="true"
            partition="persist:firecat"
            useragent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
          />
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------
export default function BrowserPage({ tabs, activeTab, tab, onGoHome, onNavigate, onAudioChange, onFallbackToProxy }) {
  const { theme }    = useTheme()
  const isHomeActive = tab?.isHome ?? true

  if (isElectron) {
    return (
      <div style={{ position: 'absolute', inset: 0, background: theme.bg }}>
        <WebviewPool
          tabs={tabs} activeTab={activeTab} isHomeActive={isHomeActive}
          onNavigate={onNavigate}
          onAudioChange={onAudioChange ?? (() => {})}
          onFallbackToProxy={onFallbackToProxy ?? (() => {})}
        />
      </div>
    )
  }

  if (isHomeActive) return null
  if (isSearchProxy(tab.url)) return <DeepResults url={tab.url} onNavigate={onNavigate} />

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: theme.bg }}>
      <iframe
        key={tab.url} src={tab.url} title={tab.title}
        style={{ flex: 1, border: 'none', width: '100%', height: '100%' }}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
        allowFullScreen
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads"
      />
    </div>
  )
}