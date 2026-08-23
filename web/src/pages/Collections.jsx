import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadLeaderboard, nameOf } from '../data.js'

function build(models) {
  const by = (key, n = 8) => [...models].sort((a, b) => (b.breakdown?.[key] ?? 0) - (a.breakdown?.[key] ?? 0)).slice(0, n)
  return [
    { title: 'Top composite', blurb: 'The highest overall scores right now.', items: [...models].sort((a, b) => a.rank - b.rank).slice(0, 8) },
    { title: 'Efficiency kings', blurb: 'Most performance per parameter and per dollar.', items: by('efficiency') },
    { title: 'Community favorites', blurb: 'Highest downloads and momentum.', items: by('community') },
    { title: 'Fresh off the press', blurb: 'Newest weights and training data.', items: by('recency') },
    { title: 'Most reproducible', blurb: 'Open code, data, and eval harness.', items: by('reproducibility') },
  ]
}

export default function Collections() {
  const [cols, setCols] = useState(null)
  useEffect(() => {
    loadLeaderboard().then((d) => setCols(build(d.models))).catch(() => setCols([]))
  }, [])

  return (
    <div className="rise">
      <h1 className="section-title">Collections</h1>
      <p className="section-sub">Hand-picked cuts of the leaderboard, computed live.</p>
      {!cols && <p style={{ color: '#9aa3b8' }}>Loading…</p>}
      {cols?.map((c) => (
        <section key={c.title} className="glass" style={{ padding: 22, marginBottom: 16 }}>
          <h2 style={{ marginTop: 0, fontSize: 20 }}>{c.title}</h2>
          <p style={{ color: '#9aa3b8', marginTop: 0 }}>{c.blurb}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 12 }}>
            {c.items.map((m) => (
              <Link key={m.model_id} to={`/model/${encodeURIComponent(m.model_id)}`} className="glass" style={{ padding: 14, display: 'block', background: 'rgba(15,15,35,.4)' }}>
                <div style={{ fontWeight: 700 }}>{nameOf(m.model_id)}</div>
                <div style={{ color: '#9aa3b8', fontSize: 13 }}>#{m.rank} · {m.composite.toFixed(1)} · {m.tier}</div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
