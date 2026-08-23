import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { loadLeaderboard, DIMS, nameOf, orgOf } from '../data.js'
import Radar from '../components/Radar.jsx'
import TierBadge from '../components/TierBadge.jsx'

export default function ModelDetail() {
  const { id } = useParams()
  const modelId = decodeURIComponent(id)
  const [model, setModel] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    loadLeaderboard()
      .then((d) => {
        const m = d.models.find((x) => x.model_id === modelId)
        if (!m) throw new Error('Model not found')
        setModel(m)
      })
      .catch((e) => setErr(e.message))
  }, [modelId])

  if (err) return <p style={{ color: '#f87171' }}>Error: {err}</p>
  if (!model) return <p style={{ color: '#9aa3b8' }}>Loading…</p>

  return (
    <div className="rise">
      <Link to="/" style={{ color: '#9aa3b8', fontSize: 14 }}>← Back to leaderboard</Link>
      <section className="glass" style={{ padding: 26, marginTop: 14, display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 240px', gap: 24, alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <TierBadge tier={model.tier} size="lg" />
            <div>
              <h1 style={{ margin: 0, fontSize: 26 }}>{nameOf(model.model_id)}</h1>
              <div style={{ color: '#9aa3b8' }}>{orgOf(model.model_id)}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '16px 0' }}>
            <span style={{ fontSize: 40, fontWeight: 900 }} className="grad-text">{model.composite.toFixed(2)}</span>
            <span style={{ color: '#9aa3b8' }}>composite · rank #{model.rank}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 12 }}>
            {DIMS.map((d) => {
              const v = model.breakdown?.[d.key] ?? 0
              return (
                <div key={d.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#9aa3b8' }}>
                    <span>{d.label}</span><span>{typeof v === 'number' ? v.toFixed(1) : v}</span>
                  </div>
                  <div style={{ height: 7, borderRadius: 5, background: 'rgba(148,163,184,.15)', overflow: 'hidden', marginTop: 4 }}>
                    <div style={{ width: `${v}%`, height: '100%', background: 'linear-gradient(90deg,#6366f1,#a855f7)' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <Radar breakdown={model.breakdown} size={220} />
        </div>
      </section>

      <section className="glass" style={{ padding: 22, marginTop: 18 }}>
        <h2 className="section-title" style={{ fontSize: 18 }}>Badges</h2>
        <p className="section-sub">Drop these into your README. Free, embeddable, always live.</p>
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'center' }}>
          <img src={model.badge_url} alt="score badge" height="28" />
          <a className="btn btn-ghost" href={model.badge_url} target="_blank" rel="noreferrer">Score SVG</a>
          <a className="btn btn-ghost" href={model.shields_url} target="_blank" rel="noreferrer">Shields endpoint</a>
        </div>
        <pre style={{ marginTop: 16, background: 'rgba(10,10,26,.7)', border: '1px solid var(--border)', borderRadius: 10, padding: 14, overflowX: 'auto', fontSize: 12, color: '#cbd5e1' }}>
{`![ModelRank](${model.badge_url})`}
        </pre>
      </section>
    </div>
  )
}
