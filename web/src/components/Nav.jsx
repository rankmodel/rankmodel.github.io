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
      <div className="glass" style={{ position: 'sticky', top: 10, margin: '10px auto', maxWidth: 1180, display: 'flex', alignItems: 'center', gap: 16, padding: '10px 16px', borderRadius: 16 }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 900, fontSize: 18 }}>
          <img src="./favicon.svg" alt="" width="30" height="30" style={{ borderRadius: 8 }} />
          <span className="grad-text">ModelRank</span>
        </Link>
        <nav style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap', marginLeft: 8 }}>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}
              style={({ isActive }) => ({
                padding: '7px 12px', borderRadius: 10, fontSize: 14, fontWeight: 600,
                color: isActive ? '#fff' : '#9aa3b8',
                background: isActive ? 'rgba(99,102,241,.18)' : 'transparent',
                border: `1px solid ${isActive ? 'rgba(129,140,248,.45)' : 'transparent'}`,
              })}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <a className="btn btn-primary pulse" href="https://rankmodel.github.io" style={{ padding: '9px 16px', fontSize: 14 }}>Get your badge</a>
      </div>
    </header>
  )
}
