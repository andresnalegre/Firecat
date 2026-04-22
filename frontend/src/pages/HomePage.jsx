import { useRef, useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import Shortcuts from '../components/Shortcuts'

// ---------------------------------------------------------------------------
// Icons — clean SVG, no emojis
// ---------------------------------------------------------------------------
const IconPerson = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconAt = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4"/>
    <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"/>
  </svg>
)
const IconMail = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
    <polyline points="22,6 12,13 2,6"/>
  </svg>
)
const IconPhone = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6.06 6.06l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
)
const IconBuilding = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <path d="M3 9h18M9 21V9"/>
  </svg>
)
const IconGlobe = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
)
const IconHash = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round">
    <line x1="4" y1="9"  x2="20" y2="9"/>
    <line x1="4" y1="15" x2="20" y2="15"/>
    <line x1="10" y1="3" x2="8"  y2="21"/>
    <line x1="16" y1="3" x2="14" y2="21"/>
  </svg>
)
const IconSearch = ({ size = 15, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)
const IconArrowUp = ({ size = 11, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="7" y1="17" x2="17" y2="7"/>
    <polyline points="7 7 17 7 17 17"/>
  </svg>
)

// ---------------------------------------------------------------------------
// Target types
// ---------------------------------------------------------------------------
const TARGET_TYPES = [
  { id: 'person',   label: 'Person',   Icon: IconPerson, placeholder: 'Full Name',            categories: 'person',   color: '#FF5722' },
  { id: 'username', label: 'Username', Icon: IconAt,     placeholder: 'username',             categories: 'username', color: '#AF52DE' },
  { id: 'email',    label: 'Email',    Icon: IconMail,   placeholder: 'Email address',       categories: 'email',    color: '#FF9500' },
  { id: 'phone',    label: 'Phone',    Icon: IconPhone,  placeholder: 'Phone number',        categories: 'phone',    color: '#34C759' },
  { id: 'domain',   label: 'Url',      Icon: IconGlobe,  placeholder: 'example.com',         categories: 'domain',   color: '#00BCD4' },
]



// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function HomePage({ onSearch }) {
  const { theme, showShortcuts } = useTheme()
  const inputRef  = useRef(null)
  const [query,    setQuery]    = useState('')
  const [typeIdx,  setTypeIdx]  = useState(0)
  const [deepMode, setDeepMode] = useState(false)
  const [focused,  setFocused]  = useState(false)

  const activeType  = TARGET_TYPES[typeIdx]
  const accentColor  = activeType.color || theme.accent
  const isDark     = theme.mode === 'dark'
  const muted      = theme.textMuted
  const border     = theme.border
  const accent     = theme.accent

  const handleSearch = (q = query, t = activeType) => {
    const trimmed = (q || '').trim()
    if (!trimmed) return
    if (deepMode) {
      onSearch(`firecat://search?q=${encodeURIComponent(trimmed)}&categories=${t.categories}`, false)
    } else {
      onSearch(trimmed, false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter')  handleSearch()
    if (e.key === 'Escape') { setShowDrop(false); inputRef.current?.blur() }
    if (e.key === 'Tab')    { e.preventDefault(); setTypeIdx(p => (p + 1) % TARGET_TYPES.length) }
  }

  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: theme.bg,
      transition: 'background-image 0.3s ease',
      backgroundImage: isDark
        ? `radial-gradient(ellipse 80% 40% at 55% 0%, ${accentColor}18 0%, transparent 65%)`
        : `radial-gradient(ellipse 80% 40% at 55% 0%, ${accentColor}10 0%, transparent 65%)`,
    }}>

      {/* Logo */}
      <img
        src="/Firecat.png"
        alt="Firecat"
        draggable="false"
        style={{
          width: 200, height: 200,
          objectFit: 'contain', marginBottom: 8,
          pointerEvents: 'none', userSelect: 'none',
          WebkitUserDrag: 'none',
        }}
      />

      {/* Tagline */}
      <p style={{
        fontSize: 13, letterSpacing: '0.04em',
        color: '#FF6B35', opacity: 0.85,
        marginBottom: 28, fontWeight: 400, margin: '0 0 22px',
        fontStyle: 'italic',
      }}>
        Let's hack the world.
      </p>

      {/* Type pills — só no modo Deep */}
      <div style={{
        display: 'flex', gap: 4,
        flexWrap: 'wrap', justifyContent: 'center',
        maxWidth: 520,
        opacity: deepMode ? 1 : 0,
        pointerEvents: deepMode ? 'auto' : 'none',
        maxHeight: deepMode ? 80 : 0,
        marginBottom: deepMode ? 10 : 0,
        overflow: 'hidden',
        transition: 'opacity 0.2s, max-height 0.25s, margin-bottom 0.2s',
      }}>
        {TARGET_TYPES.map((t, i) => {
          const isActive = i === typeIdx
          return (
            <button
              key={t.id}
              onClick={() => { setTypeIdx(i); inputRef.current?.focus() }}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '5px 11px', borderRadius: 6,
                border: `1px solid ${isActive ? accentColor + '55' : border}`,
                background: isActive
                  ? (isDark ? `${accentColor}15` : `${accentColor}0d`)
                  : 'transparent',
                color: isActive ? accentColor : muted,
                fontSize: 12, fontWeight: isActive ? 500 : 400,
                cursor: 'pointer', transition: 'all 0.15s',
                fontFamily: 'inherit',
              }}
            >
              <t.Icon size={12} color={isActive ? accentColor : muted} />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Input */}
      <div style={{ position: 'relative', width: 'min(540px, 90vw)' }}>
        <div style={{
          display: 'flex', alignItems: 'center',
          height: 46, borderRadius: 10,
          border: `1px solid ${focused ? (deepMode ? accentColor + '80' : 'rgba(255,255,255,0.5)') : border}`,
          background: isDark
            ? (focused ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.04)')
            : (focused ? '#fff' : 'rgba(0,0,0,0.03)'),
          boxShadow: focused
            ? (deepMode ? `0 0 0 3px ${accentColor}20, 0 4px 20px rgba(0,0,0,0.12)` : `0 0 0 3px rgba(255,255,255,0.08), 0 4px 20px rgba(0,0,0,0.12)`)
            : '0 1px 4px rgba(0,0,0,0.06)',
          transition: 'all 0.2s',
          paddingLeft: 14, paddingRight: 5,
          gap: 8,
        }}>
          {deepMode && <activeType.Icon size={15} color={focused ? accentColor : muted} />}

          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={deepMode ? activeType.placeholder : 'What do you want to search today?'}
            autoFocus
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: theme.text, fontSize: 14,
              fontFamily: 'inherit', caretColor: deepMode ? accentColor : '#ffffff',
            }}
          />

          {/* Deep/Normal toggle — subtle pill */}
          <button
            onClick={() => { setDeepMode(p => !p); inputRef.current?.focus() }}
            title={deepMode ? 'Deep Search active — click to switch to normal' : 'Normal search — click to switch to deep'}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '3px 9px', borderRadius: 5,
              border: `1px solid ${deepMode ? accentColor + '40' : border}`,
              background: deepMode ? `${accentColor}12` : 'transparent',
              color: deepMode ? accentColor : (isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'),
              fontSize: 11, cursor: 'pointer',
              transition: 'all 0.15s', fontFamily: 'inherit', flexShrink: 0,
            }}
          >
            <span style={{
              width: 5, height: 5, borderRadius: '50%',
              background: deepMode ? accentColor : muted,
              display: 'inline-block', opacity: deepMode ? 0.9 : 0.35,
            }} />
            {deepMode ? 'Deep' : 'Normal'}
          </button>

          {/* Search button */}
          <button
            onClick={() => handleSearch()}
            style={{
              width: 34, height: 34, borderRadius: 7, border: 'none',
              background: query.trim() ? (deepMode ? accentColor : 'rgba(255,255,255,0.15)') : (isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)'),
              color: query.trim() ? '#fff' : muted,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: query.trim() ? 'pointer' : 'default',
              transition: 'all 0.2s', flexShrink: 0,
              boxShadow: query.trim() && deepMode ? `0 2px 8px ${accentColor}40` : 'none',
            }}
          >
            <IconSearch size={14} color={query.trim() ? '#fff' : muted} />
          </button>
        </div>
      </div>

      {/* Shortcuts */}
      {showShortcuts && (
        <div style={{ marginTop: 36 }}>
          <Shortcuts onNavigate={url => onSearch(url, false)} />
        </div>
      )}
    </div>
  )
}