import { useState, useEffect, useCallback } from 'react'
import { historyService } from '../services/history'

export function useHistory() {
  const [history, setHistory] = useState([])

  const fetch = useCallback(async () => {
    try {
      const data = await historyService.list()
      setHistory(data)
    } catch {}
  }, [])

  useEffect(() => { fetch() }, [])

  const clear = useCallback(async () => {
    await historyService.clear()
    setHistory([])
  }, [])

  return { history, fetch, clear }
}