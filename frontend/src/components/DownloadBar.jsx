import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'

const isElectron  = Boolean(window.firecat)
const STORAGE_KEY = 'firecat_downloads'

function FileIcon({ color }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  )
}

function readStorage() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}

function writeStorage(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
    window.dispatchEvent(new CustomEvent('firecat-downloads-updated'))
  } catch {}
}

export default function DownloadBar() {
  const { theme } = useTheme()

  const [sessionDownloads, setSessionDownloads] = useState([])
  const [hidden, setHidden] = useState(new Set())

  useEffect(() => {
    if (!isElectron) return

    window.firecat.onDownloadProgress((data) => {
      const isFinished = data.state === 'completed' || data.state === 'interrupted' || data.state === 'cancelled'

      const current = readStorage()
      const idx     = current.findIndex(d => d.id === data.id)
      const entry   = {
        ...data,
        completedAt: isFinished
          ? new Date().toISOString()
          : (idx !== -1 ? current[idx].completedAt : null),
      }

      if (idx !== -1) {
        const updated = [...current]
        updated[idx] = entry
        writeStorage(updated)
      } else {
        writeStorage([...current, entry])
      }

      setSessionDownloads(prev => {
        const si = prev.findIndex(d => d.id === data.id)
        const sessionEntry = {
          ...data,
          completedAt: isFinished
            ? new Date().toISOString()
            : (si !== -1 ? prev[si].completedAt : null),
        }
        if (si !== -1) {
          const updated = [...prev]
          updated[si] = sessionEntry
          return updated
        }
        setHidden(h => { const next = new Set(h); next.delete(data.id); return next })
        return [...prev, sessionEntry]
      })
    })

    return () => window.firecat.removeDownloadListeners?.()
  }, [])

  const visible = sessionDownloads.filter(d => !hidden.has(d.id))

  if (!isElectron || visible.length === 0) return null

  const bg     = theme.mode === 'dark' ? '#1c1c1e' : '#f8f8f8'
  const border = theme.border
  const muted  = theme.textMuted

  const hideItem = (id) => setHidden(prev => new Set([...prev, id]))
  const hideAll  = () => setHidden(new Set(sessionDownloads.map(d => d.id)))

  return (
    <div style={{
      background: bg,
      borderTop: `1px solid ${border}`,
      userSelect: 'none',
      height: 44,
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      gap: 8,
    }}>
      <div style={{
        display: 'flex', gap: 6, flex: 1,
        overflowX: 'auto', alignItems: 'center',
        scrollbarWidth: 'none',
      }}>
        {[...visible].reverse().map((d) => {
          const pct    = d.total > 0 ? Math.round((d.received / d.total) * 100) : 0
          const done   = d.state === 'completed'
          const failed = d.state === 'interrupted' || d.state === 'cancelled'

          return (
            <div key={d.id} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: theme.mode === 'dark' ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)',
              borderRadius: 8, padding: '4px 8px',
              border: `1px solid ${border}`,
              flexShrink: 0, width: 180,
            }}>
              <span style={{ fontSize: 12, flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                {done ? '✅' : failed ? '❌' : <FileIcon color={theme.accent} />}
              </span>
              <div style={{ flex: 1, overflow: 'hidden', minWidth: 0 }}>
                <div style={{
                  fontSize: 11, fontWeight: 600, color: theme.text,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {d.filename}
                </div>
                {!done && !failed && (
                  <div style={{
                    height: 2, borderRadius: 1, marginTop: 3,
                    background: theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%', borderRadius: 1,
                      background: theme.accent, width: `${pct}%`,
                      transition: 'width 0.3s ease',
                    }} />
                  </div>
                )}
                <div style={{
                  fontSize: 9, marginTop: 1,
                  color: done ? '#34c759' : failed ? '#ff3b30' : muted,
                }}>
                  {done ? 'Complete' : failed ? 'Failed' : `${pct}%`}
                </div>
              </div>
              <button
                onClick={() => hideItem(d.id)}
                title="Hide from bar"
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: muted, fontSize: 13, padding: 0,
                  flexShrink: 0, lineHeight: 1,
                }}
              >×</button>
            </div>
          )
        })}
      </div>

      <button
        onClick={hideAll}
        title="Hide bar"
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: muted, fontSize: 20, padding: '0 4px',
          lineHeight: 1, flexShrink: 0,
        }}
      >×</button>
    </div>
  )
}