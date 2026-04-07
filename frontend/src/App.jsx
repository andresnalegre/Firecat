import { useState, useCallback, useEffect, useRef } from 'react'
import { ThemeProvider, useTheme } from './context/ThemeContext'
import { DownloadsProvider } from './context/DownloadsContext'

import TabBar       from './components/TabBar'
import NavBar       from './components/NavBar'
import SidePanel    from './components/SidePanel'
import StatusBar    from './components/StatusBar'
import Notification from './components/Notification'
import DownloadBar  from './components/DownloadBar'
import HomePage     from './pages/HomePage'
import BrowserPage  from './pages/BrowserPage'

import { useBrowser }   from './hooks/useBrowser'
import { useBookmarks } from './hooks/useBookmarks'
import { useHistory }   from './hooks/useHistory'

const isElectron = Boolean(window.firecat)

function BrowserShell() {
  const { theme } = useTheme()

  const {
    tabs, activeTab, currentTab,
    navigate, goBack, goForward, reload, goHome,
    addTab, closeTab, switchTab,
    canGoBack, canGoForward, fallbackToProxy,
    localHistory, MAX_TABS,
  } = useBrowser()

  const { bookmarks, add: addBookmark, remove: removeBookmark, toggle: toggleBookmark, isBookmarked } = useBookmarks()
  const { history, fetch: fetchHistory, clear: clearHistory } = useHistory()

  const [sidePanel,    setSidePanel]    = useState(null)
  const [notification, setNotification] = useState(null)
  const [audioTabs,    setAudioTabs]    = useState({})
  const [isFullscreen, setIsFullscreen] = useState(
    isElectron ? (window.firecat.isFullscreen?.() ?? false) : false
  )

  const pollingRef = useRef(null)

  useEffect(() => {
    if (!isElectron) return
    const cleanup = window.firecat.onFullscreenChange?.((val) => setIsFullscreen(val))
    return () => cleanup?.()
  }, [])

  useEffect(() => {
    if (sidePanel === 'history') {
      fetchHistory()
      pollingRef.current = setInterval(() => fetchHistory(), 2000)
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [sidePanel, fetchHistory])

  const notify = useCallback((msg) => {
    setNotification(msg)
    setTimeout(() => setNotification(null), 2500)
  }, [])

  const handleAudioChange = useCallback((tabId, isPlaying) => {
    setAudioTabs(prev => {
      if (prev[tabId] === isPlaying) return prev
      return { ...prev, [tabId]: isPlaying }
    })
  }, [])

  const handleBookmarkToggle = useCallback(async () => {
    if (!currentTab?.url) return
    const was = isBookmarked(currentTab.url)
    await toggleBookmark(currentTab)
    notify(was ? 'Bookmark removed' : 'Bookmark added ⭐')
  }, [currentTab, isBookmarked, toggleBookmark, notify])

  const handlePanel = useCallback((p) => {
    setSidePanel(prev => prev === p ? null : p)
  }, [])

  useEffect(() => {
    const fn = (e) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 't') { e.preventDefault(); addTab() }
        if (e.key === 'w') { e.preventDefault(); closeTab(activeTab) }
        if (e.key === 'd') { e.preventDefault(); handleBookmarkToggle() }
        if (e.key === 'h') { e.preventDefault(); handlePanel('history') }
      }
    }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [activeTab, addTab, closeTab, handleBookmarkToggle, handlePanel])

  return (
    <div style={{
      width: '100vw', height: '100vh',
      display: 'flex', flexDirection: 'column',
      background: theme.bg, color: theme.text,
      fontFamily: "'Syne', 'Segoe UI', sans-serif",
      overflow: 'hidden', position: 'relative',
    }}>
      <TabBar
        tabs={tabs}
        activeTab={activeTab}
        onSwitch={switchTab}
        onClose={closeTab}
        onAdd={addTab}
        maxTabs={MAX_TABS}
        audioTabs={audioTabs}
        isFullscreen={isFullscreen}
      />

      <NavBar
        currentTab={currentTab}
        localHistory={localHistory}
        onNavigate={navigate}
        onGoHome={goHome}
        onBack={goBack}
        onForward={goForward}
        onReload={reload}
        canGoBack={canGoBack}
        canGoForward={canGoForward}
        onBookmarkToggle={handleBookmarkToggle}
        isBookmarked={isBookmarked(currentTab?.url)}
        onPanelToggle={handlePanel}
        activePanel={sidePanel}
      />

      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>

        {currentTab?.isHome && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 2 }}>
            <HomePage onSearch={navigate} />
          </div>
        )}

        <BrowserPage
          tabs={tabs}
          activeTab={activeTab}
          tab={currentTab}
          onGoHome={goHome}
          onNavigate={navigate}
          onAudioChange={handleAudioChange}
          onFallbackToProxy={fallbackToProxy}
        />

        {sidePanel && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 10, pointerEvents: 'none' }}>
            <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, pointerEvents: 'auto' }}>
              <SidePanel
                panel={sidePanel}
                onClose={() => setSidePanel(null)}
                bookmarks={bookmarks}
                history={history}
                onNavigate={navigate}
                onBookmarkAdd={async (data) => { await addBookmark(data); notify('Bookmark added ⭐') }}
                onBookmarkRemove={async (id) => { await removeBookmark(id) }}
                onHistoryClear={async () => { await clearHistory(); notify('History cleared') }}
              />
            </div>
          </div>
        )}
      </div>

      <DownloadBar />
      <StatusBar />
      <Notification message={notification} />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <DownloadsProvider>
        <BrowserShell />
      </DownloadsProvider>
    </ThemeProvider>
  )
}