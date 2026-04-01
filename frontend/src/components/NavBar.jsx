import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { cleanUrl } from '../hooks/useBrowser'

const isElectron = Boolean(window.firecat)

const IconBack = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
)
const IconForward = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
)
const IconReload = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
  </svg>
)
const IconHome = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
)
const IconStar = ({ color, filled }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill={filled ? color : 'none'} stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
  </svg>
)
const IconBookmarks = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>
)
const IconHistory = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
)
const IconCustomize = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="13.5" cy="6.5"  r="1.5" fill={color}/>
    <circle cx="17.5" cy="10.5" r="1.5" fill={color}/>
    <circle cx="8.5"  cy="7.5"  r="1.5" fill={color}/>
    <circle cx="6.5"  cy="12.5" r="1.5" fill={color}/>
    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>
  </svg>
)
const IconMenu = ({ color }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round">
    <circle cx="12" cy="5"  r="1" fill={color}/>
    <circle cx="12" cy="12" r="1" fill={color}/>
    <circle cx="12" cy="19" r="1" fill={color}/>
  </svg>
)

function AboutModal({ onClose, onNavigate, theme }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: theme.mode === 'dark' ? '#1c1c1e' : '#fff',
          border: `1px solid ${theme.border}`,
          borderRadius: 20,
          padding: '40px 48px',
          width: 360,
          textAlign: 'center',
          boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
          position: 'relative',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 14, right: 14,
            width: 28, height: 28, borderRadius: '50%',
            border: 'none', cursor: 'pointer',
            background: theme.mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
            color: theme.textMuted, fontSize: 16, lineHeight: 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background 0.15s',
          }}
          onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)'}
          onMouseLeave={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}
        >
          ×
        </button>

        <img
          src="/Firecat.png"
          alt="Firecat"
          draggable="false"
          style={{ width: 80, height: 80, objectFit: 'contain', marginBottom: 16, pointerEvents: 'none' }}
        />

        <div style={{ fontSize: 22, fontWeight: 700, color: theme.text, marginBottom: 4 }}>
          Firecat Browser
        </div>
        <div style={{
          display: 'inline-block', fontSize: 11, fontWeight: 600,
          color: theme.textMuted,
          background: theme.mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
          borderRadius: 20, padding: '3px 12px', marginBottom: 24,
          letterSpacing: 1,
        }}>
          Version 1.0.0
        </div>

        <div style={{
          borderTop: `1px solid ${theme.border}`,
          paddingTop: 20, marginBottom: 20,
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <div style={{ fontSize: 13, color: theme.textMuted }}>
            Developed by{' '}
            <span
              onClick={() => { onClose(); onNavigate('https://andresnicolas.com') }}
              style={{ color: theme.accent, cursor: 'pointer', fontWeight: 600 }}
            >
              Andres Nicolas
            </span>
          </div>
        </div>

        <div style={{
          borderTop: `1px solid ${theme.border}`,
          paddingTop: 16, marginBottom: 24,
        }}>
          <div style={{ fontSize: 11, color: theme.textMuted, lineHeight: 1.7 }}>
            Firecat is an open-source project built using
            <br />
            Electron · React · Django
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            width: '100%', padding: '10px 0',
            borderRadius: 10, border: 'none',
            background: theme.accent, color: '#fff',
            fontSize: 14, fontWeight: 600, cursor: 'pointer',
            transition: 'opacity 0.15s',
          }}
          onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
          onMouseLeave={e => e.currentTarget.style.opacity = '1'}
        >
          Close
        </button>
      </div>
    </div>
  )
}

export default function NavBar({
  currentTab, localHistory, onNavigate, onGoHome,
  onBack, onForward, onReload,
  canGoBack, canGoForward,
  onBookmarkToggle, isBookmarked, onPanelToggle, activePanel,
}) {
  const { theme } = useTheme()
  const [urlInput,      setUrlInput]      = useState('')
  const [focused,       setFocused]       = useState(false)
  const [suggestions,   setSuggestions]   = useState([])
  const [menuOpen,      setMenuOpen]      = useState(false)
  const [clearing,      setClearing]      = useState(false)
  const [showAbout,     setShowAbout]     = useState(false)
  const [isFullscreen,  setIsFullscreen]  = useState(
    isElectron ? (window.firecat.isFullscreen?.() ?? false) : false
  )
  const inputRef = useRef(null)
  const menuRef  = useRef(null)

  useEffect(() => {
    if (!isElectron) return
    window.firecat.onFullscreenChange?.((val) => setIsFullscreen(val))
  }, [])

  useEffect(() => {
    const fn = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', fn)
    return () => document.removeEventListener('mousedown', fn)
  }, [])

  const displayValue = focused
    ? urlInput
    : cleanUrl(currentTab?.url || '')

  const handleSubmit = (e) => {
    e.preventDefault()
    setSuggestions([])
    if (urlInput.trim()) onNavigate(urlInput.trim())
  }

  const handleChange = (e) => {
    const val = e.target.value
    setUrlInput(val)
    if (val.length > 1) {
      const q = val.toLowerCase()
      setSuggestions(
        localHistory
          .filter(h => h.url.toLowerCase().includes(q) || h.title?.toLowerCase().includes(q))
          .slice(0, 6)
      )
    } else {
      setSuggestions([])
    }
  }

  const btn = (active, disabled = false) => ({
    width: 34, height: 34, borderRadius: 8, border: 'none',
    background: active ? `${theme.accent}33` : 'transparent',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
    cursor: disabled ? 'default' : 'pointer',
    opacity: disabled ? 0.3 : 1,
    transition: 'background 0.15s, opacity 0.15s',
    WebkitAppRegion: 'no-drag',
  })

  const iconColor      = theme.textMuted
  const navPaddingLeft = isElectron && !isFullscreen ? '6px' : '10px'

  const toolBtns = [
    { icon: <IconBookmarks color={activePanel === 'bookmarks' ? theme.accent : iconColor} />, panel: 'bookmarks', tip: 'Bookmarks' },
    { icon: <IconHistory   color={activePanel === 'history'   ? theme.accent : iconColor} />, panel: 'history',   tip: 'History'   },
    { icon: <IconCustomize color={activePanel === 'customize' ? theme.accent : iconColor} />, panel: 'customize', tip: 'Customize'  },
  ]

  const menuItems = [
    {
      label: 'Downloads',
      shortcut: '⌥⌘L',
      action: () => {
        onNavigate('firecat://downloads')
        setMenuOpen(false)
      },
    },
    {
      label: clearing ? 'Clearing...' : 'Clear cache & cookies',
      action: async () => {
        if (clearing) return
        setClearing(true)
        try {
          if (isElectron && window.firecat?.clearCache) {
            await window.firecat.clearCache()
          } else {
            if (window.caches) {
              const keys = await caches.keys()
              await Promise.all(keys.map(k => caches.delete(k)))
            }
          }
        } catch {}
        setClearing(false)
        onReload()
        setMenuOpen(false)
      },
    },
    { type: 'divider' },
    {
      label: 'Developer Tools',
      shortcut: '⌥⌘I',
      action: () => {
        if (isElectron && window.firecat?.openDevTools) {
          window.firecat.openDevTools()
        }
        setMenuOpen(false)
      },
    },
    { type: 'divider' },
    {
      label: 'About Firecat',
      action: () => {
        setShowAbout(true)
        setMenuOpen(false)
      },
    },
  ]

  const menuBg    = theme.mode === 'dark' ? '#2c2c2e' : '#fff'
  const menuHover = theme.mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'
  const menuText  = theme.text
  const menuMuted = theme.textMuted

  return (
    <>
      {showAbout && (
        <AboutModal
          onClose={() => setShowAbout(false)}
          onNavigate={onNavigate}
          theme={theme}
        />
      )}

      <div style={{
        display: 'flex', alignItems: 'center', gap: 4,
        padding: `6px 10px 6px ${navPaddingLeft}`,
        background: theme.tabBar, borderBottom: `1px solid ${theme.border}`,
        WebkitAppRegion: 'drag',
      }}>

        <button style={btn(false, !canGoBack)} onClick={canGoBack ? onBack : undefined} title="Back">
          <IconBack color={iconColor} />
        </button>

        <button style={btn(false, !canGoForward)} onClick={canGoForward ? onForward : undefined} title="Forward">
          <IconForward color={iconColor} />
        </button>

        <button style={btn(false)} onClick={onReload} title="Reload">
          <IconReload color={iconColor} />
        </button>

        <button style={btn(false)} onClick={onGoHome} title="Home">
          <IconHome color={iconColor} />
        </button>

        <form onSubmit={handleSubmit} style={{ flex: 1, position: 'relative', WebkitAppRegion: 'no-drag' }}>
          <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
            {currentTab?.isHome
              ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2.5" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            }
          </span>

          <input
            ref={inputRef}
            value={displayValue}
            placeholder="Search or type a URL"
            onFocus={() => {
              setFocused(true)
              setUrlInput(cleanUrl(currentTab?.url || ''))
              setTimeout(() => inputRef.current?.select(), 10)
            }}
            onBlur={() => { setFocused(false); setTimeout(() => setSuggestions([]), 150) }}
            onChange={handleChange}
            style={{
              width: '100%', height: 36, borderRadius: 20, border: 'none', outline: 'none',
              background: focused
                ? (theme.mode === 'dark' ? '#3c3c3e' : '#fff')
                : (theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.07)'),
              color: theme.text, padding: '0 38px 0 34px', fontSize: 13,
              transition: 'all 0.2s', boxShadow: focused ? `0 0 0 2px ${theme.accent}55` : 'none',
              WebkitAppRegion: 'no-drag',
            }}
          />

          {currentTab?.url && !currentTab?.isHome && (
            <button
              type="button"
              onClick={onBookmarkToggle}
              title={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
              style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 4,
                WebkitAppRegion: 'no-drag',
              }}
            >
              <IconStar color={isBookmarked ? '#FBBC05' : iconColor} filled={isBookmarked} />
            </button>
          )}

          {suggestions.length > 0 && (
            <div style={{
              position: 'absolute', top: 40, left: 0, right: 0, zIndex: 100,
              background: theme.mode === 'dark' ? '#2c2c2e' : '#fff',
              border: `1px solid ${theme.border}`, borderRadius: 10,
              boxShadow: '0 8px 24px rgba(0,0,0,0.2)', overflow: 'hidden',
              WebkitAppRegion: 'no-drag',
            }}>
              {suggestions.map((s, i) => (
                <div
                  key={i}
                  onMouseDown={() => { setUrlInput(s.url); setSuggestions([]); onNavigate(s.url) }}
                  style={{
                    padding: '9px 14px', cursor: 'pointer', fontSize: 12, color: theme.text,
                    borderBottom: i < suggestions.length - 1 ? `1px solid ${theme.border}` : 'none',
                  }}
                >
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.title || s.url}</div>
                  <div style={{ opacity: 0.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.url}</div>
                </div>
              ))}
            </div>
          )}
        </form>

        {toolBtns.map(({ icon, panel, tip }) => (
          <button key={panel} style={btn(activePanel === panel)} onClick={() => onPanelToggle(panel)} title={tip}>
            {icon}
          </button>
        ))}

        <div ref={menuRef} style={{ position: 'relative', WebkitAppRegion: 'no-drag' }}>
          <button style={btn(menuOpen)} onClick={() => setMenuOpen(p => !p)} title="Menu">
            <IconMenu color={iconColor} />
          </button>

          {menuOpen && (
            <div style={{
              position: 'absolute', top: 38, right: 0, zIndex: 200,
              background: menuBg, border: `1px solid ${theme.border}`,
              borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
              minWidth: 210, overflow: 'hidden', padding: '4px 0',
              WebkitAppRegion: 'no-drag',
            }}>
              {menuItems.map((item, i) => {
                if (item.type === 'divider') {
                  return <div key={i} style={{ height: 1, background: theme.border, margin: '4px 0' }} />
                }
                return (
                  <div
                    key={i}
                    onClick={item.action}
                    onMouseEnter={e => e.currentTarget.style.background = menuHover}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    style={{
                      padding: '9px 16px', cursor: 'pointer', fontSize: 13,
                      color: menuText,
                      display: 'flex', alignItems: 'center',
                      justifyContent: 'space-between', gap: 16,
                      transition: 'background 0.1s', background: 'transparent',
                      opacity: clearing && item.label.includes('Clear') ? 0.6 : 1,
                    }}
                  >
                    <span>{item.label}</span>
                    {item.shortcut && (
                      <span style={{ fontSize: 11, color: menuMuted, flexShrink: 0 }}>
                        {item.shortcut}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </>
  )
}