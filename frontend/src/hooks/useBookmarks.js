import { useState, useEffect, useCallback } from 'react'
import { bookmarksService } from '../services/bookmarks'

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState([])

  useEffect(() => {
    bookmarksService.list().then(setBookmarks).catch(() => {})
  }, [])

  const add = useCallback(async (data) => {
    const created = await bookmarksService.add(data)
    setBookmarks(prev => [created, ...prev])
    return created
  }, [])

  const remove = useCallback(async (id) => {
    await bookmarksService.remove(id)
    setBookmarks(prev => prev.filter(b => b.id !== id))
  }, [])

  const isBookmarked = useCallback((url) =>
    bookmarks.some(b => b.url === url), [bookmarks])

  const toggle = useCallback(async (tab) => {
    if (!tab?.url) return
    const existing = bookmarks.find(b => b.url === tab.url)
    if (existing) await remove(existing.id)
    else await add({ title: tab.title, url: tab.url })
  }, [bookmarks, add, remove])

  return { bookmarks, add, remove, toggle, isBookmarked }
}