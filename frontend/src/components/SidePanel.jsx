import { useState, useEffect } from 'react'
import { useTheme, THEMES } from '../context/ThemeContext'
import { historyService } from '../services/history'

function HistoryPanel({ history, onNavigate, onClose, onClear, onDeleteOne, theme }) {
  const [selected,   setSelected]   = useState(new Set())
  const [selectMode, setSelectMode] = useState(false)

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    if (selected.size === history.length) setSelected(new Set())
    else setSelected(new Set(history.map(h => h.id)))
  }

  const deleteSelected = async () => {
    for (const id of selected) await onDeleteOne(id)
    setSelected(new Set())
    setSelectMode(false)
  }

  const grouped = history.reduce((acc, h) => {
    const date      = h.visited_at ? new Date(h.visited_at) : new Date()
    const now       = new Date()
    const today     = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
    const itemDay   = new Date(date.getFullYear(), date.getMonth(), date.getDate())

    let label
    if (itemDay.getTime() === today.getTime()) label = 'Today'
    else if (itemDay.getTime() === yesterday.getTime()) label = 'Yesterday'
    else label = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })

    if (!acc[label]) acc[label] = []
    acc[label].push(h)
    return acc
  }, {})

  const rowBase = {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '10px 12px', borderRadius: 10, marginBottom: 4,
    cursor: 'pointer', transition: 'background 0.1s',
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14, gap: 8 }}>
        <button
          onClick={() => { setSelectMode(p => !p); setSelected(new Set()) }}
          style={{ background: 'none', border: 'none', fontSize: 12, color: theme.accent, cursor: 'pointer' }}
        >
          {selectMode ? 'Cancel' : 'Select'}
        </button>

        {selectMode && history.length > 0 && (
          <button
            onClick={selectAll}
            style={{ background: 'none', border: 'none', fontSize: 12, color: theme.textMuted, cursor: 'pointer' }}
          >
            {selected.size === history.length ? 'Deselect all' : 'Select all'}
          </button>
        )}

        {history.length > 0 && (
          <button
            onClick={onClear}
            style={{ background: 'none', border: 'none', fontSize: 12, color: '#ff3b30', cursor: 'pointer', marginLeft: 'auto' }}
          >
            Clear all
          </button>
        )}
      </div>

      {selectMode && selected.size > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 14px', borderRadius: 10, marginBottom: 14,
          background: `${theme.accent}22`, border: `1px solid ${theme.accent}44`,
        }}>
          <span style={{ fontSize: 13, color: theme.text }}>{selected.size} selected</span>
          <button
            onClick={deleteSelected}
            style={{ background: '#ff3b30', border: 'none', borderRadius: 6, color: '#fff', fontSize: 12, padding: '4px 14px', cursor: 'pointer', fontWeight: 600 }}
          >
            Delete
          </button>
        </div>
      )}

      {history.length === 0 && (
        <div style={{ textAlign: 'center', opacity: 0.4, padding: '40px 0', fontSize: 13, color: theme.text }}>
          No history yet
        </div>
      )}

      {Object.entries(grouped).map(([label, entries]) => (
        <div key={label} style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 600, opacity: 0.45, textTransform: 'uppercase', letterSpacing: 1, color: theme.text, marginBottom: 8 }}>
            {label}
          </div>

          {entries.map((h, i) => {
            const isSelected = selected.has(h.id)
            return (
              <div
                key={h.id ?? i}
                onClick={() => {
                  if (selectMode) { toggleSelect(h.id); return }
                  onNavigate(h.url); onClose()
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)'
                  const btn = e.currentTarget.querySelector('.h-del-btn')
                  if (btn) btn.style.opacity = '0.5'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = isSelected
                    ? `${theme.accent}18`
                    : (theme.mode === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)')
                  const btn = e.currentTarget.querySelector('.h-del-btn')
                  if (btn) btn.style.opacity = '0'
                }}
                style={{
                  ...rowBase,
                  background: isSelected
                    ? `${theme.accent}18`
                    : (theme.mode === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'),
                  border: `1px solid ${isSelected ? theme.accent + '55' : theme.border}`,
                }}
              >
                {selectMode && (
                  <div style={{
                    width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                    background: isSelected ? theme.accent : 'transparent',
                    border: `2px solid ${isSelected ? theme.accent : theme.border}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}>
                    {isSelected && (
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    )}
                  </div>
                )}

                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: theme.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {h.title}
                  </div>
                  <div style={{ fontSize: 11, opacity: 0.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {h.url}
                  </div>
                  {h.visited_at && (
                    <div style={{ fontSize: 10, opacity: 0.3, marginTop: 2, color: theme.text }}>
                      {new Date(h.visited_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  )}
                </div>

                {!selectMode && (
                  <button
                    className="h-del-btn"
                    onClick={(e) => { e.stopPropagation(); onDeleteOne(h.id) }}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      opacity: 0, fontSize: 15, color: theme.textMuted,
                      padding: '4px 6px', borderRadius: '50%',
                      transition: 'opacity 0.15s, background 0.15s',
                      flexShrink: 0, lineHeight: 1,
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.opacity = 1
                      e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.opacity = '0.5'
                      e.currentTarget.style.background = 'transparent'
                    }}
                  >×</button>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

export default function SidePanel({
  panel, onClose, bookmarks, history,
  onNavigate, onBookmarkAdd, onBookmarkRemove, onHistoryClear,
}) {
  const { theme, setThemeByName, showShortcuts, toggleShortcuts } = useTheme()
  const [newTitle,     setNewTitle]     = useState('')
  const [newUrl,       setNewUrl]       = useState('')
  const [localHistory, setLocalHistory] = useState(history)

  useEffect(() => { setLocalHistory(history) }, [history])

  const handleDeleteOne = async (id) => {
    setLocalHistory(prev => prev.filter(h => h.id !== id))
    try {
      await historyService.deleteOne(id)
    } catch (e) {
      setLocalHistory(history)
      console.warn('delete failed', e)
    }
  }

  const row = {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: 12, borderRadius: 10, marginBottom: 6,
    background: theme.mode === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
    border: `1px solid ${theme.border}`,
  }
  const inp = {
    width: '100%', padding: '9px 12px', borderRadius: 10,
    border: `1.5px solid ${theme.border}`,
    background: theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : '#f8f9fa',
    color: theme.text, fontSize: 13, outline: 'none', marginBottom: 8,
  }
  const sectionLabel = {
    fontSize: 11, fontWeight: 600, opacity: 0.5,
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 10,
  }
  const divider = { borderTop: `1px solid ${theme.border}`, margin: '16px 0' }

  const TITLES = { customize: 'Customize', bookmarks: 'Bookmarks', history: 'History' }

  const handleAddBookmark = () => {
    if (!newUrl.trim()) return
    let url = newUrl.trim()
    if (!url.startsWith('http://') && !url.startsWith('https://')) url = `https://${url}`
    onBookmarkAdd({ title: newTitle.trim() || url, url })
    setNewTitle(''); setNewUrl('')
  }

  return (
    <div style={{
      position: 'absolute', right: 0, top: 0, bottom: 0, width: 340,
      background: theme.mode === 'dark' ? '#1c1c1e' : '#fff',
      boxShadow: '-4px 0 32px rgba(0,0,0,0.25)', zIndex: 50,
      display: 'flex', flexDirection: 'column',
      borderLeft: `1px solid ${theme.border}`,
    }}>

      <div style={{
        padding: '18px 18px 14px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: `1px solid ${theme.border}`,
      }}>
        <span style={{ fontSize: 17, fontWeight: 700, color: theme.text }}>{TITLES[panel]}</span>
        <button
          onClick={onClose}
          onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.14)'}
          onMouseLeave={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}
          style={{
            width: 36, height: 36, borderRadius: '50%', border: 'none',
            background: theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
            color: theme.text, fontSize: 18, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background 0.15s', flexShrink: 0,
          }}
        >×</button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>

        {panel === 'customize' && (
          <>
            <div style={sectionLabel}>Themes</div>
            {Object.values(THEMES).map((t) => (
              <div key={t.name} onClick={() => setThemeByName(t.name)} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: 12,
                borderRadius: 12, cursor: 'pointer', marginBottom: 8,
                background: theme.name === t.name ? `${theme.accent}22` : 'transparent',
                border: `1.5px solid ${theme.name === t.name ? theme.accent : theme.border}`,
                transition: 'all 0.15s',
              }}>
                <div style={{
                  width: 44, height: 32, borderRadius: 8,
                  background: t.bg, border: `2px solid ${t.accent}`,
                  flexShrink: 0,
                }} />
                <div style={{ fontSize: 13, fontWeight: 600, color: theme.text }}>
                  {t.name}
                </div>
              </div>
            ))}

            <div style={divider} />

            <div style={sectionLabel}>Shortcuts on home</div>
            <div style={{ ...row, cursor: 'pointer' }} onClick={toggleShortcuts}>
              <span style={{ fontSize: 13, color: theme.text }}>Show shortcuts</span>
              <div style={{
                width: 38, height: 22, borderRadius: 11,
                background: showShortcuts ? theme.accent : (theme.mode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)'),
                position: 'relative', transition: 'background 0.2s',
              }}>
                <div style={{
                  position: 'absolute', top: 3,
                  left: showShortcuts ? 18 : 3,
                  width: 16, height: 16, borderRadius: '50%',
                  background: '#fff', transition: 'left 0.2s',
                }} />
              </div>
            </div>
          </>
        )}

        {panel === 'bookmarks' && (
          <>
            <div style={sectionLabel}>Your bookmarks</div>
            {bookmarks.length === 0 && (
              <div style={{ textAlign: 'center', opacity: 0.4, padding: '30px 0', fontSize: 13 }}>No bookmarks yet</div>
            )}
            {bookmarks.map((b) => (
              <div key={b.id} style={row}>
                <div style={{ flex: 1, cursor: 'pointer', overflow: 'hidden' }} onClick={() => { onNavigate(b.url); onClose() }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: theme.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.title}</div>
                  <div style={{ fontSize: 11, opacity: 0.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.url}</div>
                </div>
                <button
                  onClick={() => onBookmarkRemove(b.id)}
                  onMouseEnter={e => e.currentTarget.style.opacity = 1}
                  onMouseLeave={e => e.currentTarget.style.opacity = '0.4'}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', opacity: 0.4, fontSize: 16, color: theme.text, padding: 6, borderRadius: '50%', transition: 'opacity 0.15s', display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, flexShrink: 0 }}
                >✕</button>
              </div>
            ))}

            <div style={divider} />
            <div style={sectionLabel}>Add bookmark</div>
            <input
              style={inp}
              placeholder="Title (e.g. Google)"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
            />
            <input
              style={inp}
              placeholder="URL (e.g. www.google.com)"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddBookmark() }}
            />
            <button
              onClick={handleAddBookmark}
              onMouseEnter={e => e.currentTarget.style.opacity = 1}
              onMouseLeave={e => e.currentTarget.style.opacity = '0.9'}
              style={{ width: '100%', padding: 10, borderRadius: 10, border: 'none', background: theme.accent, color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', opacity: 0.9, transition: 'opacity 0.15s' }}
            >Add</button>
          </>
        )}

        {panel === 'history' && (
          <HistoryPanel
            history={localHistory}
            onNavigate={onNavigate}
            onClose={onClose}
            onClear={onHistoryClear}
            onDeleteOne={handleDeleteOne}
            theme={theme}
          />
        )}
      </div>
    </div>
  )
}