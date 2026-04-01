import { useTheme } from '../context/ThemeContext'

const SHORTCUTS = [
  {
    name: 'YouTube',
    url: 'https://www.youtube.com',
    renderSvg: () => (
      <svg height="36px" width="36px" viewBox="0 0 461.001 461.001">
        <path
          fill="#F61C0D"
          d="M365.257,67.393H95.744C42.866,67.393,0,110.259,0,163.137v134.728
            c0,52.878,42.866,95.744,95.744,95.744h269.513c52.878,0,95.744-42.866,95.744-95.744V163.137
            C461.001,110.259,418.135,67.393,365.257,67.393z"
        />
        <path
          fill="white"
          d="M300.506,237.056l-126.06,60.123
            c-3.359,1.602-7.239-0.847-7.239-4.568V168.607c0-3.774,3.982-6.22,7.348-4.514l126.06,63.881
            C304.363,229.873,304.298,235.248,300.506,237.056z"
        />
      </svg>
    ),
  },
  {
    name: 'Instagram',
    url: 'https://www.instagram.com',
    svg: (
      <svg viewBox="0 0 32 32" width="36" height="36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="ig1" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(12 23) rotate(-55.3758) scale(25.5196)">
            <stop stopColor="#B13589"/>
            <stop offset="0.793" stopColor="#C62F94"/>
            <stop offset="1" stopColor="#8A3AC8"/>
          </radialGradient>
          <radialGradient id="ig2" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(11 31) rotate(-65.1363) scale(22.5942)">
            <stop stopColor="#E0E8B7"/>
            <stop offset="0.4447" stopColor="#FB8A2E"/>
            <stop offset="0.7147" stopColor="#E2425C"/>
            <stop offset="1" stopColor="#E2425C" stopOpacity="0"/>
          </radialGradient>
          <radialGradient id="ig3" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(0.5 3) rotate(-8.1301) scale(38.8909 8.31836)">
            <stop offset="0.1567" stopColor="#406ADC"/>
            <stop offset="0.4678" stopColor="#6A45BE"/>
            <stop offset="1" stopColor="#6A45BE" stopOpacity="0"/>
          </radialGradient>
        </defs>
        <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#ig1)"/>
        <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#ig2)"/>
        <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#ig3)"/>
        <circle cx="21.5" cy="10.5" r="1.5" fill="white"/>
        <circle cx="16" cy="16" r="3" stroke="white" strokeWidth="2" fill="none"/>
        <rect x="6" y="6" width="20" height="20" rx="5" stroke="white" strokeWidth="2" fill="none"/>
      </svg>
    ),
  },
  {
    name: 'Reddit',
    url: 'https://www.reddit.com',
    svg: (
      <svg viewBox="0 0 32 32" fill="none" width="36" height="36">
        <circle cx="16" cy="16" r="14" fill="#FC471E"/>
        <path fillRule="evenodd" clipRule="evenodd" d="M20.0193 8.90951C20.0066 8.98984 20 9.07226 20 9.15626C20 10.0043 20.6716 10.6918 21.5 10.6918C22.3284 10.6918 23 10.0043 23 9.15626C23 8.30819 22.3284 7.6207 21.5 7.6207C21.1309 7.6207 20.7929 7.7572 20.5315 7.98359L16.6362 7L15.2283 12.7651C13.3554 12.8913 11.671 13.4719 10.4003 14.3485C10.0395 13.9863 9.54524 13.7629 9 13.7629C7.89543 13.7629 7 14.6796 7 15.8103C7 16.5973 7.43366 17.2805 8.06967 17.6232C8.02372 17.8674 8 18.1166 8 18.3696C8 21.4792 11.5817 24 16 24C20.4183 24 24 21.4792 24 18.3696C24 18.1166 23.9763 17.8674 23.9303 17.6232C24.5663 17.2805 25 16.5973 25 15.8103C25 14.6796 24.1046 13.7629 23 13.7629C22.4548 13.7629 21.9605 13.9863 21.5997 14.3485C20.2153 13.3935 18.3399 12.7897 16.2647 12.7423L17.3638 8.24143L20.0193 8.90951ZM12.5 18.8815C13.3284 18.8815 14 18.194 14 17.3459C14 16.4978 13.3284 15.8103 12.5 15.8103C11.6716 15.8103 11 16.4978 11 17.3459C11 18.194 11.6716 18.8815 12.5 18.8815ZM19.5 18.8815C20.3284 18.8815 21 18.194 21 17.3459C21 16.4978 20.3284 15.8103 19.5 15.8103C18.6716 15.8103 18 16.4978 18 17.3459C18 18.194 18.6716 18.8815 19.5 18.8815ZM12.7773 20.503C12.5476 20.3462 12.2372 20.4097 12.084 20.6449C11.9308 20.8802 11.9929 21.198 12.2226 21.3548C13.3107 22.0973 14.6554 22.4686 16 22.4686C17.3446 22.4686 18.6893 22.0973 19.7773 21.3548C20.0071 21.198 20.0692 20.8802 19.916 20.6449C19.7628 20.4097 19.4524 20.3462 19.2226 20.503C18.3025 21.1309 17.1513 21.4449 16 21.4449C14.6827 21.4449 13.4155 21.1309 12.7773 20.503Z" fill="white"/>
      </svg>
    ),
  },
  {
    name: 'LinkedIn',
    url: 'https://www.linkedin.com',
    svg: (
      <svg viewBox="0 0 32 32" fill="none" width="36" height="36">
        <rect width="32" height="32" rx="4" fill="#0A66C2"/>
        <path fill="white" d="M7 12h3.5v11H7V12zm1.75-1.5a2 2 0 110-4 2 2 0 010 4zM13 12h3.3v1.5h.05c.46-.87 1.58-1.8 3.25-1.8 3.48 0 4.12 2.29 4.12 5.27V23H20.2v-5.3c0-1.26-.02-2.88-1.75-2.88-1.76 0-2.03 1.37-2.03 2.79V23H13V12z"/>
      </svg>
    ),
  },
  {
    name: 'Twitter',
    url: 'https://www.twitter.com',
    darkInner: true,
    svg: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
    ),
  },
  {
    name: 'Google',
    url: 'https://www.google.com',
    svg: (
      <svg viewBox="0 0 48 48" width="36" height="36">
        <path fill="#FBBC05" d="M9.827 24c0-1.524.253-2.986.705-4.356l-7.909-6.04A23.787 23.787 0 000 24c0 3.736.868 7.261 2.623 10.396l7.905-6.04A13.788 13.788 0 019.827 24"/>
        <path fill="#EB4335" d="M23.714 10.133c3.311 0 6.302 1.174 8.652 3.094l6.836-6.827C35.036 2.773 29.695.533 23.714.533c-9.287 0-17.268 5.311-21.09 13.071l7.909 6.04c1.822-5.532 7.017-9.511 13.181-9.511"/>
        <path fill="#34A853" d="M23.714 37.867c-6.164 0-11.359-3.979-13.181-9.511l-7.909 6.04c3.822 7.76 11.803 13.071 21.09 13.071 5.732 0 11.205-2.035 15.312-5.882l-7.507-5.814c-2.118 1.334-4.785 2.096-7.805 2.096"/>
        <path fill="#4285F4" d="M46.145 24c0-1.387-.213-2.88-.533-4.267H23.714v9.067h12.604c-.612 3.081-2.297 5.544-4.797 7.214l7.507 5.814C43.333 37.614 46.145 31.649 46.145 24"/>
      </svg>
    ),
  },
]

export default function Shortcuts({ onNavigate }) {
  const { theme } = useTheme()
  const isDark    = theme.mode === 'dark'
  const circleBg  = isDark ? '#2e2e2e' : '#f0f0f0'
  const border    = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)'
  const shadow    = isDark ? '0 4px 12px rgba(0,0,0,0.5)' : '0 4px 6px rgba(0,0,0,0.1)'

  return (
    <div style={{
      display: 'flex', flexWrap: 'nowrap',
      justifyContent: 'center', alignItems: 'center', gap: '12px',
    }}>
      {SHORTCUTS.map((sc) => {
        const icon = sc.renderSvg ? sc.renderSvg(isDark) : sc.svg

        return (
          <div
            key={sc.name}
            onClick={() => onNavigate(sc.url)}
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, cursor: 'pointer', flexShrink: 0 }}
          >
            <div
              style={{
                width: 60, height: 60, borderRadius: '50%',
                background: circleBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: shadow,
                border: `1px solid ${border}`,
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.1)'
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)'
                e.currentTarget.style.boxShadow = shadow
              }}
            >
              {sc.darkInner ? (
                <div style={{
                  width: 38, height: 38, borderRadius: '50%',
                  background: '#000',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {icon}
                </div>
              ) : icon}
            </div>
            <span style={{
              fontSize: 11,
              color: isDark ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.5)',
              textAlign: 'center', whiteSpace: 'nowrap',
            }}>
              {sc.name}
            </span>
          </div>
        )
      })}
    </div>
  )
}