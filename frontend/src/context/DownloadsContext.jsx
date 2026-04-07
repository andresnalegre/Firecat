import { createContext, useContext, useState, useCallback } from 'react'

const STORAGE_KEY = 'firecat_downloads'

function readStorage() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}

function writeStorage(list) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {}
}

const DownloadsContext = createContext(null)

export function DownloadsProvider({ children }) {
  const [downloads, setDownloads] = useState(readStorage)

  const upsert = useCallback((entry) => {
    setDownloads(prev => {
      const idx = prev.findIndex(d => d.id === entry.id)
      const next = idx !== -1
        ? prev.map((d, i) => i === idx ? entry : d)
        : [...prev, entry]
      writeStorage(next)
      return next
    })
  }, [])

  const remove = useCallback((id) => {
    setDownloads(prev => {
      const next = prev.filter(d => d.id !== id)
      writeStorage(next)
      return next
    })
  }, [])

  const clear = useCallback(() => {
    setDownloads([])
    writeStorage([])
  }, [])

  return (
    <DownloadsContext.Provider value={{ downloads, upsert, remove, clear }}>
      {children}
    </DownloadsContext.Provider>
  )
}

export const useDownloads = () => useContext(DownloadsContext)