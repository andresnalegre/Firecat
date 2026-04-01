import { useRef, useEffect, useState, useCallback } from 'react'
import { useTheme } from '../context/ThemeContext'

const isElectron = Boolean(window.firecat)

function SoundBars() {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 1.5, marginLeft: 2 }}>
      <style>{`
        @keyframes sb1{0%,100%{height:3px}50%{height:9px}}
        @keyframes sb2{0%,100%{height:7px}50%{height:2px}}
        @keyframes sb3{0%,100%{height:4px}25%{height:9px}75%{height:2px}}
      `}</style>
      {[
        { anim: 'sb1', delay: '0s' },
        { anim: 'sb2', delay: '0.15s' },
        { anim: 'sb3', delay: '0.3s' },
      ].map((b, i) => (
        <span key={i} style={{
          display: 'inline-block', width: 2, height: 5,
          background: '#4285F4', borderRadius: 1,
          animationName: b.anim,
          animationDuration: '0.7s',
          animationTimingFunction: 'ease-in-out',
          animationIterationCount: 'infinite',
          animationDelay: b.delay,
        }} />
      ))}
    </span>
  )
}

export default function TabBar({ tabs, activeTab, onSwitch, onClose, onAdd, maxTabs, audioTabs = {}, isFullscreen = false }) {
  const { theme } = useTheme()
  const scrollRef    = useRef(null)
  const containerRef = useRef(null)
  const [showLeft,       setShowLeft]       = useState(false)
  const [showRight,      setShowRight]      = useState(false)
  const [containerWidth, setContainerWidth] = useState(800)
  const [hoveredTab,     setHoveredTab]     = useState(null)

  const TAB_MIN  = 40
  const TAB_MAX  = 200
  const TAB_CTRL = 120

  const availableWidth = containerWidth - TAB_CTRL
  const rawTabWidth    = availableWidth / tabs.length
  const tabWidth       = Math.max(TAB_MIN, Math.min(TAB_MAX, rawTabWidth))
  const needsScroll    = tabWidth <= TAB_MIN && tabs.length > 1
  const showTitle      = tabWidth > 80
  const showClose      = tabWidth > 60

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => setContainerWidth(entry.contentRect.width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const checkScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    setShowLeft(el.scrollLeft > 4)
    setShowRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4)
  }, [])

  useEffect(() => {
    checkScroll()
    const el = scrollRef.current
    el?.addEventListener('scroll', checkScroll)
    return () => el?.removeEventListener('scroll', checkScroll)
  }, [tabs, checkScroll])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const activeEl = el.querySelector(`[data-tab-index="${activeTab}"]`)
    if (activeEl) activeEl.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' })
  }, [activeTab])

  const scrollBy = (dir) => scrollRef.current?.scrollBy({ left: dir * 200, behavior: 'smooth' })

  const handleMouseDown = (e, i) => {
    if (e.button === 1) { e.preventDefault(); if (i > 0) onClose(i) }
  }

  const arrowBtn = {
    width: 22, height: 22, borderRadius: '50%', border: 'none',
    background: theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
    color: theme.textMuted, fontSize: 13, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    WebkitAppRegion: 'no-drag',
  }

  return (
    <div
      ref={containerRef}
      style={{
        background: theme.tabBar,
        display: 'flex', alignItems: 'center',
        padding: '8px 8px 0', gap: 2, minHeight: 44,
        userSelect: 'none', borderBottom: `1px solid ${theme.border}`,
        width: '100%', overflow: 'hidden',
        WebkitAppRegion: 'drag',
      }}
    >
      <style>{`
        .fc-tab-scroll::-webkit-scrollbar { display: none; }
        .fc-close:hover { background: ${theme.mode === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.15)'} !important; opacity: 1 !important; }
        .fc-tab:hover { background: ${theme.mode === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'} !important; }
        .fc-add:hover { background: ${theme.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'} !important; }
      `}</style>

      {!isElectron && (
        <div style={{
          display: 'flex', gap: 6, padding: '0 8px 8px',
          flexShrink: 0, WebkitAppRegion: 'no-drag',
        }}>
          {['#FF5F56', '#FFBD2E', '#27C93F'].map((c, i) => (
            <div key={i} style={{ width: 12, height: 12, borderRadius: '50%', background: c }} />
          ))}
        </div>
      )}

      {isElectron && (
        <div style={{
          width: isFullscreen ? 0 : 90,
          flexShrink: 0,
          paddingBottom: 8,
          WebkitAppRegion: 'drag',
          transition: 'width 0.2s',
          overflow: 'hidden',
        }} />
      )}

      {needsScroll && showLeft && (
        <button style={arrowBtn} onClick={() => scrollBy(-1)}>‹</button>
      )}

      <div
        ref={scrollRef}
        className="fc-tab-scroll"
        style={{
          display: 'flex', flex: 1, gap: 1,
          overflowX: needsScroll ? 'auto' : 'hidden',
          overflowY: 'hidden', alignItems: 'flex-end',
          scrollbarWidth: 'none',
          WebkitAppRegion: 'no-drag',
        }}
      >
        {tabs.map((tab, i) => {
          const active    = i === activeTab
          const hovered   = hoveredTab === i
          const canClose  = i > 0
          const showX     = canClose && (active || hovered) && (showClose || hovered || active)
          const isPlaying = audioTabs[tab.id]

          return (
            <div
              key={tab.id}
              data-tab-index={i}
              className={active ? '' : 'fc-tab'}
              onClick={() => onSwitch(i)}
              onMouseDown={(e) => handleMouseDown(e, i)}
              onMouseEnter={() => setHoveredTab(i)}
              onMouseLeave={() => setHoveredTab(null)}
              title={tab.title}
              style={{
                display: 'flex', alignItems: 'center',
                justifyContent: showTitle ? 'flex-start' : 'center',
                gap: 5, padding: showTitle ? '7px 8px 7px 10px' : '7px 4px',
                borderRadius: '10px 10px 0 0', cursor: 'pointer',
                width: tabWidth, minWidth: tabWidth, maxWidth: tabWidth,
                flexShrink: 0,
                background: active ? theme.bg : 'transparent',
                color: active ? theme.text : theme.textMuted,
                transition: 'background 0.12s, color 0.12s',
                borderTop: active ? `2px solid ${theme.accent}` : '2px solid transparent',
                position: 'relative', overflow: 'hidden', boxSizing: 'border-box',
                WebkitAppRegion: 'no-drag',
              }}
            >
              <span style={{ fontSize: 13, flexShrink: 0, lineHeight: 1 }}>{tab.favicon}</span>

              {showTitle && (
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>
                  {tab.title}
                </span>
              )}

              {isPlaying && !showX && <SoundBars />}

              {showX ? (
                <span
                  className="fc-close"
                  onClick={(e) => { e.stopPropagation(); onClose(i) }}
                  style={{
                    flexShrink: 0, width: 16, height: 16,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    borderRadius: '50%', fontSize: 13, lineHeight: 1,
                    cursor: 'pointer', opacity: 0.6, background: 'transparent',
                    transition: 'background 0.12s, opacity 0.12s', color: theme.text,
                    WebkitAppRegion: 'no-drag',
                  }}
                >×</span>
              ) : (
                canClose && !isPlaying && <span style={{ width: 16, flexShrink: 0 }} />
              )}

              {active && (
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: theme.bg }} />
              )}
            </div>
          )
        })}

        {tabs.length < maxTabs && (
          <button
            className="fc-add"
            onClick={onAdd}
            title="New tab (Ctrl+T)"
            style={{
              width: 28, height: 28, borderRadius: '8px 8px 0 0', border: 'none',
              background: 'transparent', color: theme.textMuted,
              fontSize: 20, fontWeight: 300,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, cursor: 'pointer', transition: 'background 0.15s',
              alignSelf: 'flex-end',
              WebkitAppRegion: 'no-drag',
            }}
          >+</button>
        )}

        {/* área de drag após os tabs */}
        <div style={{
          flex: 1,
          minWidth: 40,
          alignSelf: 'stretch',
          WebkitAppRegion: 'drag',
        }} />
      </div>

      {needsScroll && showRight && (
        <button style={arrowBtn} onClick={() => scrollBy(1)}>›</button>
      )}
    </div>
  )
}