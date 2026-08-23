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
      <div style={{ maxWidth: 1140, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, height: 60, borderBottom: '1px solid var(--border)' }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 9, fontWeight: 800, fontSize: 17 }}>
            <img src="./favicon.svg" alt="" width="26" height="26" style={{ borderRadius: 7 }} />
            <span className="grad-text">ModelRank</span>
          </Link>
          <nav style={{ display: 'flex', gap: 2, flex: 1, flexWrap: 'wrap', marginLeft: 8, overflowX: 'auto' }}>
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'}
                style={({ isActive }) => ({
                  padding: '6px 11px', borderRadius: 8, fontSize: 13.5, fontWeight: 500, whiteSpace: 'nowrap',
                  color: isActive ? 'var(--accent-ink)' : 'var(--muted)',
                  background: isActive ? 'var(--accent-soft)' : 'transparent',
                })}>
                {l.label}
              </NavLink>
            ))}
          </nav>
          <a className="btn btn-primary" href="https://rankmodel.github.io" style={{ padding: '8px 14px', fontSize: 13.5 }}>Get your badge</a>
        </div>
      </div>
    </header>
  )
}
