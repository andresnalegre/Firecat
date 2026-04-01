import { useTheme } from '../context/ThemeContext'

export default function StatusBar() {
  const { theme } = useTheme()

  return (
    <div style={{
      height: 22, background: theme.tabBar,
      borderTop: `1px solid ${theme.border}`,
      display: 'flex', alignItems: 'center',
      justifyContent: 'center',
      fontSize: 11, color: theme.textMuted,
    }}>
      Firecat Browser
    </div>
  )
}