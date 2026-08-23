export default function Api() {
  const endpoints = [
    { m: 'GET', p: '/leaderboard.json', d: 'Full leaderboard: composite, tier, rank, and 5-dimension breakdown for every model.' },
    { m: 'GET', p: '/badges/{org}/{model}/score.svg', d: 'Embeddable score badge for a model.' },
    { m: 'GET', p: '/badges/{org}/{model}/tier.svg', d: 'Tier badge (S/A/B/C/D).' },
    { m: 'GET', p: '/badges/{org}/{model}/rank.svg', d: 'Rank badge.' },
    { m: 'GET', p: '/badges/{org}/{model}/shields.json', d: 'Shields.io endpoint for live badges.' },
    { m: 'GET', p: '/models/{org}/{model}.json', d: 'Per-model score data.' },
  ]
  return (
    <div className="rise">
      <h1 className="section-title">API</h1>
      <p className="section-sub">All rankings are public and static. No key required.</p>

      <section className="glass" style={{ padding: 24, marginBottom: 18 }}>
        <h2 style={{ marginTop: 0 }}>Endpoints</h2>
        <div style={{ display: 'grid', gap: 10 }}>
          {endpoints.map((e) => (
            <div key={e.p} style={{ display: 'flex', gap: 14, alignItems: 'baseline', borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#22d3ee', minWidth: 44 }}>{e.m}</span>
              <code style={{ color: '#c7d2fe', minWidth: 280 }}>{e.p}</code>
              <span style={{ color: '#9aa3b8', fontSize: 14 }}>{e.d}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="glass" style={{ padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>Example</h2>
        <pre style={{ background: 'rgba(10,10,26,.7)', border: '1px solid var(--border)', borderRadius: 10, padding: 16, overflowX: 'auto', fontSize: 13, color: '#cbd5e1' }}>
{`fetch('https://rankmodel.github.io/leaderboard.json')
  .then(r => r.json())
  .then(d => console.log(d.models.length, 'models'));`}
        </pre>
        <p style={{ color: '#9aa3b8' }}>Raw rankings are also published as CSV for full reproducibility.</p>
      </section>
    </div>
  )
}
