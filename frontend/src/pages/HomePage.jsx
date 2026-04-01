import { useRef, useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import Shortcuts from '../components/Shortcuts'

export default function HomePage({ onSearch }) {
  const { theme, showShortcuts } = useTheme()
  const inputRef = useRef(null)
  const [hackerMode, setHackerMode] = useState(false)

  const hackerGreen = theme.mode === 'dark' ? '#00ff41' : '#007a20'

  const handleSearch = (value) => {
    if (!value.trim()) return
    onSearch(value.trim(), hackerMode)
  }

  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      gap: 24, background: theme.bg,
      backgroundImage: theme.mode === 'dark'
        ? `radial-gradient(ellipse at 60% 20%, ${theme.accent}18 0%, transparent 60%),
           radial-gradient(ellipse at 20% 80%, ${theme.accent}0a 0%, transparent 50%)`
        : `radial-gradient(ellipse at 60% 20%, ${theme.accent}10 0%, transparent 60%)`,
    }}>

      <img
        src="/Firecat.png"
        alt="Firecat"
        draggable="false"
        onDragStart={(e) => e.preventDefault()}
        style={{
          width: 280, height: 280,
          objectFit: 'contain', marginBottom: -8,
          userSelect: 'none',
          WebkitUserDrag: 'none',
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'relative', width: 'min(580px, 90vw)' }}>

        <span style={{
          position: 'absolute', left: 18, top: '50%',
          transform: 'translateY(-50%)',
          fontSize: 16, opacity: 0.4, pointerEvents: 'none',
        }}>🔍</span>

        <input
          ref={inputRef}
          autoFocus
          placeholder="What do you want to search today?"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSearch(e.target.value)
          }}
          onFocus={(e) => e.target.style.borderColor = theme.accent}
          onBlur={(e) => e.target.style.borderColor = theme.mode === 'dark'
            ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.15)'}
          style={{
            width: '100%', height: 52, borderRadius: 26,
            border: `2px solid ${theme.mode === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.15)'}`,
            background: theme.inputBg,
            color: theme.text,
            fontFamily: 'inherit',
            padding: '0 56px 0 46px',
            fontSize: 15, outline: 'none',
            boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
            transition: 'all 0.25s',
            caretColor: theme.text,
          }}
        />

        {/* hacker mode toggle */}
        <button
          onClick={() => { setHackerMode(p => !p); inputRef.current?.focus() }}
          title={hackerMode ? 'Switch to normal search' : 'Switch to deep search'}
          style={{
            position: 'absolute', right: 8, top: '50%',
            transform: 'translateY(-50%)',
            width: 36, height: 36, borderRadius: '50%',
            border: `1.5px solid ${hackerMode ? hackerGreen : theme.border}`,
            background: hackerMode
              ? (theme.mode === 'dark' ? 'rgba(0,255,65,0.12)' : 'rgba(0,122,32,0.1)')
              : 'transparent',
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s',
            boxShadow: hackerMode ? `0 0 10px ${hackerGreen}44` : 'none',
            pointerEvents: 'auto',
          }}
        >
          {hackerMode ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke={hackerGreen} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="4 17 10 11 4 5"/>
              <line x1="12" y1="19" x2="20" y2="19"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke={theme.textMuted} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
          )}
        </button>

        {/* mode label */}
        <div style={{
          position: 'absolute', bottom: -22, right: 8,
          fontSize: 10,
          color: hackerMode ? hackerGreen : theme.textMuted,
          fontFamily: 'inherit',
          opacity: hackerMode ? 1 : 0.6,
          transition: 'all 0.2s',
          display: 'flex', alignItems: 'center', gap: 5,
          letterSpacing: 0.5,
          pointerEvents: 'none',
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            background: hackerMode ? hackerGreen : theme.textMuted,
            display: 'inline-block', flexShrink: 0,
            boxShadow: hackerMode ? `0 0 6px ${hackerGreen}` : 'none',
            transition: 'all 0.2s',
          }} />
          {hackerMode ? 'deep search' : 'normal search'}
        </div>
      </div>

      {showShortcuts && (
        <div style={{ marginTop: 8 }}>
          <Shortcuts onNavigate={(url) => onSearch(url, false)} />
        </div>
      )}
    </div>
  )
}