import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { useDownloads } from '../context/DownloadsContext'

function FileIcon({ ext, size = 32 }) {
  const colors = {
    pdf:  '#FF3B30', zip: '#FF9500', rar: '#FF9500',
    mp4:  '#AF52DE', mp3: '#AF52DE', mov: '#AF52DE',
    jpg:  '#34C759', png: '#34C759', gif: '#34C759', webp: '#34C759',
    doc:  '#007AFF', docx: '#007AFF', xls: '#34C759', xlsx: '#34C759',
    ppt:  '#FF9500', pptx: '#FF9500',
    js:   '#FFD60A', ts: '#007AFF', py: '#34C759', html: '#FF6B35',
  }
  const color = colors[ext?.toLowerCase()] || '#8E8E93'

  return (
    <div style={{
      width: size, height: size, borderRadius: size * 0.22,
      background: `${color}22`, border: `1.5px solid ${color}44`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <svg width={size * 0.5} height={size * 0.5} viewBox="0 0 24 24" fill="none"
        stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
    </div>
  )
}

function getExt(filename) {
  return filename?.split('.').pop() || ''
}

function groupByDate(downloads) {
  const groups = {}
  ;[...downloads].reverse().forEach(d => {
    const date  = d.completedAt ? new Date(d.completedAt) : new Date()
    const now   = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yest  = new Date(today); yest.setDate(today.getDate() - 1)
    const day   = new Date(date.getFullYear(), date.getMonth(), date.getDate())

    let label
    if (day.getTime() === today.getTime())     label = 'Today'
    else if (day.getTime() === yest.getTime()) label = 'Yesterday'
    else label = date.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })

    if (!groups[label]) groups[label] = []
    groups[label].push(d)
  })
  return groups
}

export default function DownloadsPage() {
  const { theme }                  = useTheme()
  const { downloads, remove, clear } = useDownloads()
  const [search, setSearch]        = useState('')
  const isElectron                 = Boolean(window.firecat)
  const muted                      = theme.textMuted

  const filtered = search.trim()
    ? downloads.filter(d => d.filename?.toLowerCase().includes(search.toLowerCase()))
    : downloads

  const grouped = groupByDate(filtered)

  return (
    <div style={{
      width: '100%', height: '100%', overflowY: 'auto',
      background: theme.bg, color: theme.text,
      fontFamily: "'Syne', 'Segoe UI', sans-serif",
    }}>
      <div style={{ maxWidth: 860, margin: '0 auto', padding: '40px 32px 80px' }}>

        <div style={{
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', marginBottom: 32,
          flexWrap: 'wrap', gap: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 42, height: 42, borderRadius: 12,
              background: `${theme.accent}22`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                stroke={theme.accent} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </div>
            <div>
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: theme.text }}>
                Download history
              </h1>
              <div style={{ fontSize: 12, color: muted, marginTop: 2 }}>
                {downloads.length} item{downloads.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {isElectron && (
              <button
                onClick={() => window.firecat.openDownloads?.()}
                style={{
                  padding: '8px 16px', borderRadius: 8,
                  border: `1.5px solid ${theme.border}`,
                  background: 'transparent', color: theme.accent,
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                Open folder
              </button>
            )}
            {downloads.length > 0 && (
              <button
                onClick={clear}
                style={{
                  padding: '8px 16px', borderRadius: 8,
                  border: `1.5px solid rgba(255,59,48,0.3)`,
                  background: 'rgba(255,59,48,0.08)', color: '#ff3b30',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                }}
              >
                Clear all
              </button>
            )}
          </div>
        </div>

        <div style={{ position: 'relative', marginBottom: 28 }}>
          <svg style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
            width="15" height="15" viewBox="0 0 24 24" fill="none"
            stroke={muted} strokeWidth="2.5" strokeLinecap="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search download history"
            style={{
              width: '100%', height: 42, borderRadius: 10,
              border: `1.5px solid ${theme.border}`,
              background: theme.mode === 'dark' ? 'rgba(255,255,255,0.06)' : '#fff',
              color: theme.text, paddingLeft: 40, paddingRight: 16,
              fontSize: 13, outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {downloads.length === 0 && (
          <div style={{ textAlign: 'center', padding: '80px 0', color: muted }}>
            <div style={{ fontSize: 56, marginBottom: 16 }}>📂</div>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: theme.text }}>No downloads yet</div>
            <div style={{ fontSize: 13 }}>Files you download will appear here</div>
          </div>
        )}

        {downloads.length > 0 && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: muted }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
            <div style={{ fontSize: 14 }}>No results for "{search}"</div>
          </div>
        )}

        {Object.entries(grouped).map(([label, items]) => (
          <div key={label} style={{ marginBottom: 32 }}>
            <div style={{
              fontSize: 13, fontWeight: 600, color: muted,
              marginBottom: 12, paddingBottom: 8,
              borderBottom: `1px solid ${theme.border}`,
            }}>
              {label}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {items.map((d) => {
                const pct    = d.total > 0 ? Math.round((d.received / d.total) * 100) : 0
                const done   = d.state === 'completed'
                const failed = d.state === 'interrupted' || d.state === 'cancelled'
                const active = d.state === 'progressing'
                const mbTot  = d.total > 0 ? (d.total / 1024 / 1024).toFixed(1) : '?'
                const mbRecv = (d.received / 1024 / 1024).toFixed(1)
                const time   = d.completedAt
                  ? new Date(d.completedAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
                  : ''
                const ext = getExt(d.filename)

                return (
                  <div
                    key={d.id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 16,
                      padding: '14px 16px', borderRadius: 12,
                      border: `1px solid ${theme.border}`,
                      background: theme.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'}
                    onMouseLeave={e => e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'}
                  >
                    <FileIcon ext={ext} size={40} />

                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{
                        fontSize: 14, fontWeight: 600, color: theme.text,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        marginBottom: 4,
                      }}>
                        {d.filename}
                      </div>

                      {active && (
                        <div style={{ marginBottom: 4 }}>
                          <div style={{
                            height: 4, borderRadius: 2,
                            background: theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                            overflow: 'hidden',
                          }}>
                            <div style={{
                              height: '100%', borderRadius: 2,
                              background: theme.accent, width: `${pct}%`,
                              transition: 'width 0.3s ease',
                            }} />
                          </div>
                        </div>
                      )}

                      <div style={{ fontSize: 11, color: muted, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                        {done   && <span style={{ color: '#34c759', fontWeight: 600 }}>✓ Complete</span>}
                        {failed && <span style={{ color: '#ff3b30', fontWeight: 600 }}>✕ Failed</span>}
                        {active && <span style={{ color: theme.accent, fontWeight: 600 }}>{pct}% · {mbRecv} / {mbTot} MB</span>}
                        {done   && <span>{mbTot} MB</span>}
                        {time   && <span>{time}</span>}
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                      {done && isElectron && (
                        <button
                          onClick={() => window.firecat.openDownloads?.()}
                          title="Show in folder"
                          style={{
                            width: 32, height: 32, borderRadius: 8, border: 'none',
                            background: 'transparent', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: muted, transition: 'all 0.15s',
                          }}
                          onMouseEnter={e => { e.currentTarget.style.background = theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.07)'; e.currentTarget.style.color = theme.text }}
                          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = muted }}
                        >
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => remove(d.id)}
                        title="Remove from history"
                        style={{
                          width: 32, height: 32, borderRadius: 8, border: 'none',
                          background: 'transparent', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: muted, transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,59,48,0.1)'; e.currentTarget.style.color = '#ff3b30' }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = muted }}
                      >
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18"/>
                          <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}