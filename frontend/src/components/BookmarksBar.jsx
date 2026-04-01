import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'

const MAX_VISIBLE = 8
const STORAGE_KEY = 'firecat_pinned_bookmarks'

const getFavicon = (url) => {
  try { return `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}&sz=16` }
  catch { return null }
}

const loadPinned = () => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') }
  catch { return [] }
}

const savePinned = (ids) => localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))

export default function BookmarksBar({ bookmarks, onNavigate }) {
  const { theme } = useTheme()
  const [showMore,   setShowMore]   = useState(false)
  const [showManage, setShowManage] = useState(false)
  const [pinnedIds,  setPinnedIds]  = useState(loadPinned)
  const dropRef   = useRef(null)
  const manageRef = useRef(null)

  useEffect(() => {
    const validIds = bookmarks.map(b => b.id)
    const cleaned  = pinnedIds.filter(id => validIds.includes(id))
    if (cleaned.length !== pinnedIds.length) {
      setPinnedIds(cleaned)
      savePinned(cleaned)
    }
  }, [bookmarks])

  useEffect(() => {
    const fn = (e) => {
      if (dropRef.current   && !dropRef.current.contains(e.target))   setShowMore(false)
      if (manageRef.current && !manageRef.current.contains(e.target)) setShowManage(false)
    }
    document.addEventListener('mousedown', fn)
    return () => document.removeEventListener('mousedown', fn)
  }, [])

  if (!bookmarks.length) return null

  const pinned   = pinnedIds.map(id => bookmarks.find(b => b.id === id)).filter(Boolean)
  const unpinned = bookmarks.filter(b => !pinnedIds.includes(b.id))
  const barFull  = pinnedIds.length >= MAX_VISIBLE

  const togglePin = (id) => {
    let updated
    if (pinnedIds.includes(id)) {
      updated = pinnedIds.filter(i => i !== id)
    } else {
      if (barFull) return
      updated = [...pinnedIds, id]
    }
    setPinnedIds(updated)
    savePinned(updated)
  }

  const isPinned = (id) => pinnedIds.includes(id)

  const showBar = pinned.length > 0 || bookmarks.length > 0

  if (!showBar) return null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 2,
      padding: '3px 10px',
      background: theme.tabBar,
      borderBottom: `1px solid ${theme.border}`,
      overflow: 'hidden', minHeight: 28,
    }}>

      {/* pinned bookmarks */}
      {pinned.map((b) => {
        const fav = getFavicon(b.url)
        return (
          <button
            key={b.id}
            onClick={() => onNavigate(b.url)}
            title={b.title}
            onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '3px 10px', borderRadius: 6, border: 'none',
              background: 'transparent', color: theme.textMuted,
              fontSize: 12, whiteSpace: 'nowrap', cursor: 'pointer',
              maxWidth: 150, overflow: 'hidden',
              transition: 'background 0.1s', flexShrink: 0,
            }}
          >
            {fav
              ? <img src={fav} width={12} height={12} style={{ borderRadius: 2, flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />
              : <span style={{ fontSize: 10, opacity: 0.5 }}>🔖</span>
            }
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{b.title}</span>
          </button>
        )
      })}

      {/* manage button */}
      <div ref={manageRef} style={{ position: 'relative', flexShrink: 0 }}>
        <button
          onClick={() => { setShowManage(p => !p); setShowMore(false) }}
          title="Manage bookmark bar"
          onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'}
          onMouseLeave={e => e.currentTarget.style.background = showManage ? (theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)') : 'transparent'}
          style={{
            display: 'flex', alignItems: 'center',
            padding: '3px 8px', borderRadius: 6, border: 'none',
            background: showManage ? (theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)') : 'transparent',
            color: theme.textMuted, cursor: 'pointer', transition: 'background 0.1s',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="3" y1="6"  x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        {showManage && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, zIndex: 300,
            width: 300, maxHeight: 420, overflowY: 'auto',
            background: theme.mode === 'dark' ? '#1c1c1e' : '#ffffff',
            border: `1px solid ${theme.border}`,
            borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            marginTop: 4,
          }}>
            <div style={{ padding: '12px 14px 10px', borderBottom: `1px solid ${theme.border}` }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: theme.text, marginBottom: 2 }}>
                Manage bookmark bar
              </div>
              <div style={{ fontSize: 11, opacity: 0.45, color: theme.text }}>
                {pinnedIds.length}/{MAX_VISIBLE} slots — click to pin/unpin
              </div>
            </div>

            <div style={{ padding: '8px 14px', borderBottom: `1px solid ${theme.border}` }}>
              <div style={{ height: 4, borderRadius: 2, background: theme.border, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 2,
                  width: `${(pinnedIds.length / MAX_VISIBLE) * 100}%`,
                  background: barFull ? '#ff3b30' : theme.accent,
                  transition: 'width 0.2s, background 0.2s',
                }} />
              </div>
            </div>

            {bookmarks.map((b) => {
              const fav    = getFavicon(b.url)
              const pinned = isPinned(b.id)
              const full   = barFull && !pinned

              return (
                <div
                  key={b.id}
                  onClick={() => togglePin(b.id)}
                  onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 14px',
                    cursor: full ? 'not-allowed' : 'pointer',
                    borderBottom: `1px solid ${theme.border}`,
                    opacity: full ? 0.4 : 1,
                    transition: 'background 0.1s, opacity 0.15s',
                  }}
                >
                  {fav
                    ? <img src={fav} width={14} height={14} style={{ borderRadius: 2, flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />
                    : <span style={{ fontSize: 12, opacity: 0.5, flexShrink: 0 }}>🔖</span>
                  }
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: theme.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {b.title}
                    </div>
                    <div style={{ fontSize: 11, opacity: 0.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {b.url}
                    </div>
                  </div>
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                    background: pinned ? theme.accent : 'transparent',
                    border: `2px solid ${pinned ? theme.accent : theme.border}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}>
                    {pinned && (
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    )}
                  </div>
                </div>
              )
            })}

            <div style={{ padding: '10px 14px', fontSize: 11, opacity: 0.35, color: theme.text, textAlign: 'center' }}>
              Changes save automatically
            </div>
          </div>
        )}
      </div>

      {/* overflow — bookmarks not pinned */}
      {unpinned.length > 0 && (
        <div ref={dropRef} style={{ position: 'relative', flexShrink: 0 }}>
          <button
            onClick={() => { setShowMore(p => !p); setShowManage(false) }}
            onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'}
            onMouseLeave={e => e.currentTarget.style.background = showMore ? (theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)') : 'transparent'}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '3px 10px', borderRadius: 6, border: 'none',
              background: showMore ? (theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)') : 'transparent',
              color: theme.textMuted, fontSize: 12,
              cursor: 'pointer', transition: 'background 0.1s',
            }}
          >
            <span>»</span>
            <span>{unpinned.length} more</span>
          </button>

          {showMore && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, zIndex: 200,
              width: 280, maxHeight: 360, overflowY: 'auto',
              background: theme.mode === 'dark' ? '#1c1c1e' : '#ffffff',
              border: `1px solid ${theme.border}`,
              borderRadius: 10, boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              marginTop: 4,
            }}>
              <div style={{ padding: '10px 14px 8px', borderBottom: `1px solid ${theme.border}`, fontSize: 11, fontWeight: 600, opacity: 0.5, textTransform: 'uppercase', letterSpacing: 1, color: theme.text }}>
                Not in bar
              </div>
              {unpinned.map((b) => {
                const fav = getFavicon(b.url)
                return (
                  <div
                    key={b.id}
                    onClick={() => { onNavigate(b.url); setShowMore(false) }}
                    onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px', cursor: 'pointer', borderBottom: `1px solid ${theme.border}`, transition: 'background 0.1s' }}
                  >
                    {fav
                      ? <img src={fav} width={14} height={14} style={{ borderRadius: 2, flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />
                      : <span style={{ fontSize: 12, opacity: 0.5, flexShrink: 0 }}>🔖</span>
                    }
                    <div style={{ overflow: 'hidden' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: theme.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.title}</div>
                      <div style={{ fontSize: 11, opacity: 0.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.url}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}