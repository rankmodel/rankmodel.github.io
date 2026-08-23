import { Link, NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Leaderboard' },
  { to: '/collections', label: 'Collections' },
  { to: '/head-to-head', label: 'Head to Head' },
  { to: '/quiz', label: 'Quiz' },
  { to: '/methodology', label: 'Methodology' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/api', label: 'API' },
]

export default function Nav() {
  return (
    <header style={{ position: 'relative', zIndex: 2 }}>
      <div style={{ maxWidth: 1120, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, height: 58, borderBottom: '1px solid var(--hair)' }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <span style={{ width: 18, height: 18, background: 'var(--accent)', borderRadius: 5, display: 'inline-block' }} />
            <span style={{ fontFamily: 'var(--display)', fontWeight: 700, fontSize: 18, letterSpacing: '-0.4px' }}>ModelRank</span>
          </Link>
          <nav style={{ display: 'flex', gap: 1, flex: 1, flexWrap: 'wrap', marginLeft: 10, overflowX: 'auto' }}>
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'}
                style={({ isActive }) => ({
                  padding: '6px 10px', borderRadius: 7, fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap',
                  color: isActive ? 'var(--ink)' : 'var(--muted)',
                  background: isActive ? '#f0efec' : 'transparent',
                })}>
                {label}
              </NavLink>
            ))}
          </nav>
          <a className="btn btn-primary" href="https://rankmodel.github.io" style={{ padding: '7px 13px', fontSize: 13 }}>Get your badge</a>
        </div>
      </div>
    </header>
  )
}
