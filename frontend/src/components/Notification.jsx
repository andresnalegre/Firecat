export default function Notification({ message }) {
  if (!message) return null

  return (
    <div style={{
      position: 'fixed', bottom: 28, left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(28,28,30,0.96)', color: '#fff',
      padding: '10px 22px', borderRadius: 20, fontSize: 13,
      zIndex: 999, boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      pointerEvents: 'none', whiteSpace: 'nowrap',
    }}>
      {message}
    </div>
  )
}