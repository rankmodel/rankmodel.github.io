import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadLeaderboard, DIMS } from '../data.js'
import ModelCard from '../components/ModelCard.jsx'

const SORTS = [
  { key: 'rank', label: 'Rank' },
  { key: 'composite', label: 'Composite' },
  { key: 'benchmarks', label: 'Benchmarks' },
  { key: 'efficiency', label: 'Efficiency' },
  { key: 'community', label: 'Community' },
  { key: 'recency', label: 'Recency' },
  { key: 'reproducibility', label: 'Reproducibility' },
]

export default function Leaderboard() {
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('rank')
  const [tier, setTier] = useState('all')

  useEffect(() => {
    loadLeaderboard().then(setData).catch((e) => setData({ error: e.message }))
  }, [])

  const models = useMemo(() => {
    if (!data || !data.models) return []
    let list = data.models.slice()
    if (q.trim()) {
      const t = q.toLowerCase()
      list = list.filter((m) => m.model_id.toLowerCase().includes(t))
    }
    if (tier !== 'all') list = list.filter((m) => m.tier === tier)
    list.sort((a, b) => {
      if (sort === 'rank') return a.rank - b.rank
      if (sort === 'composite') return b.composite - a.composite
      return (b.breakdown?.[sort] ?? 0) - (a.breakdown?.[sort] ?? 0)
    })
    return list
  }, [data, q, sort, tier])

  return (
    <div className="rise">
      <section className="glass" style={{ position: 'relative', overflow: 'hidden', textAlign: 'center', padding: '46px 20px 34px', borderRadius: 22, marginBottom: 22 }}>
        <h1 style={{ fontSize: 'clamp(30px,6vw,50px)', fontWeight: 900, letterSpacing: '-1.5px', margin: 0 }}>
          <span className="grad-text">ModelRank</span>
        </h1>
        <p style={{ fontSize: 'clamp(15px,2.4vw,19px)', color: '#dbe2ef', maxWidth: 760, margin: '16px auto 0', lineHeight: 1.6 }}>
          The independent leaderboard for open HuggingFace models. Composite 5-dimension scoring, free embeddable badges, and zero paid placements.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap', marginTop: 22 }}>
          <a className="btn btn-primary" href="https://rankmodel.github.io">Score a model</a>
          <a className="btn btn-ghost" href="./api">Read the API</a>
        </div>
        <div style={{ marginTop: 20, fontSize: 13, color: '#cbd5e1' }}>
          <span className="pill">{data?.total ?? '…'} models ranked</span>{' '}
          <span className="pill">5 scoring dimensions</span>{' '}
          <span className="pill">0 paid placements</span>
        </div>
      </section>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 18 }}>
        <input className="input" style={{ flex: 1, minWidth: 220 }} placeholder="Search models…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="select" value={sort} onChange={(e) => setSort(e.target.value)}>
          {SORTS.map((s) => <option key={s.key} value={s.key}>Sort: {s.label}</option>)}
        </select>
        <select className="select" value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="all">All tiers</option>
          {['S', 'A', 'B', 'C', 'D'].map((t) => <option key={t} value={t}>Tier {t}</option>)}
        </select>
      </div>

      {!data && <p style={{ color: '#9aa3b8' }}>Loading leaderboard…</p>}
      {data?.error && <p style={{ color: '#f87171' }}>Error: {data.error}</p>}
      {data && (
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {models.map((m, i) => <ModelCard key={m.model_id} model={m} index={i} />)}
        </div>
      )}
      {data && models.length === 0 && <p style={{ color: '#9aa3b8' }}>No models match your filters.</p>}
    </div>
  )
}
