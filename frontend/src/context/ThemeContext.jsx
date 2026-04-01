import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { preferencesService } from '../services/preferences'

export const THEMES = {
  'Firecat Dark': {
    name: 'Firecat Dark', bg: '#0f0f0f', tabBar: '#1a1a1a', accent: '#FF5722',
    text: '#ffffff', textMuted: 'rgba(255,255,255,0.5)', inputBg: '#2a2a2a',
    shortcutBg: '#1e1e1e', border: 'rgba(255,255,255,0.07)', mode: 'dark',
  },
  'Chrome Dark': {
    name: 'Chrome Dark', bg: '#202124', tabBar: '#292a2d', accent: '#8ab4f8',
    text: '#e8eaed', textMuted: 'rgba(255,255,255,0.45)', inputBg: '#303134',
    shortcutBg: '#2c2c2e', border: 'rgba(255,255,255,0.08)', mode: 'dark',
  },
  'Midnight Blue': {
    name: 'Midnight Blue', bg: '#0d1117', tabBar: '#161b22', accent: '#58a6ff',
    text: '#c9d1d9', textMuted: 'rgba(201,209,217,0.45)', inputBg: '#21262d',
    shortcutBg: '#161b22', border: 'rgba(255,255,255,0.07)', mode: 'dark',
  },
  'Light Classic': {
    name: 'Light Classic', bg: '#f8f9fa', tabBar: '#dee1e6', accent: '#1a73e8',
    text: '#202124', textMuted: 'rgba(0,0,0,0.5)', inputBg: '#ffffff',
    shortcutBg: '#ffffff', border: 'rgba(0,0,0,0.1)', mode: 'light',
  },
  'Warm Sand': {
    name: 'Warm Sand', bg: '#fdf6ec', tabBar: '#e8ddd0', accent: '#c0392b',
    text: '#2c1810', textMuted: 'rgba(0,0,0,0.45)', inputBg: '#ffffff',
    shortcutBg: '#fffdf9', border: 'rgba(0,0,0,0.09)', mode: 'light',
  },
}

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [theme, setTheme]                 = useState(THEMES['Firecat Dark'])
  const [showShortcuts, setShowShortcuts] = useState(true)

  useEffect(() => {
    preferencesService.get()
      .then((p) => {
        if (p?.theme && THEMES[p.theme]) setTheme(THEMES[p.theme])
        if (typeof p?.show_shortcuts === 'boolean') setShowShortcuts(p.show_shortcuts)
      })
      .catch(() => {})
  }, [])

  const savePrefs = useCallback((patch) => {
    preferencesService.save(patch).catch(console.warn)
  }, [])

  const setThemeByName = useCallback((name) => {
    const t = THEMES[name]
    if (!t) return
    setTheme(t)
    savePrefs({ theme: t.name, mode: t.mode, bg_color: t.bg, accent: t.accent })
  }, [savePrefs])

  const toggleShortcuts = useCallback(() => {
    setShowShortcuts((prev) => {
      savePrefs({ show_shortcuts: !prev })
      return !prev
    })
  }, [savePrefs])

  return (
    <ThemeContext.Provider value={{ theme, setThemeByName, showShortcuts, toggleShortcuts }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)