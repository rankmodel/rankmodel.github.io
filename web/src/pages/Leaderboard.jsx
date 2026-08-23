import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadLeaderboard, DIMS } from '../data.js'
import ModelRow from '../components/ModelCard.jsx'

const COLS = [
  { key: 'rank', label: 'Rank', sort: (m) => m.rank, cls: '' },
  { key: 'model', label: 'Model', sort: (m) => m.model_id.toLowerCase(), cls: '' },
  { key: 'tier', label: 'Tier', sort: (m) => m.tier, cls: '' },
  { key: 'composite', label: 'Composite', sort: (m) => m.composite, cls: '' },
  { key: 'benchmarks', label: 'Bench', sort: (m) => m.breakdown?.benchmarks ?? 0, cls: '' },
  { key: 'efficiency', label: 'Effic', sort: (m) => m.breakdown?.efficiency ?? 0, cls: '' },
  { key: 'community', label: 'Comm', sort: (m) => m.breakdown?.community ?? 0, cls: '' },
  { key: 'recency', label: 'Recency', sort: (m) => m.breakdown?.recency ?? 0, cls: 'hide-sm' },
  { key: 'reproducibility', label: 'Repro', sort: (m) => m.breakdown?.reproducibility ?? 0, cls: 'hide-sm' },
  { key: 'badge', label: 'Badge', sort: null, cls: 'hide-sm' },
]

export default function Leaderboard() {
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')
  const [tier, setTier] = useState('all')
  const [sortKey, setSortKey] = useState('rank')
  const [dir, setDir] = useState('asc')

  useEffect(() => {
    loadLeaderboard().then(setData).catch((e) => setData({ error: e.message }))
  }, [])

  const rows = useMemo(() => {
    if (!data || !data.models) return []
    let list = data.models.slice()
    if (q.trim()) {
      const t = q.toLowerCase()
      list = list.filter((m) => m.model_id.toLowerCase().includes(t))
    }
    if (tier !== 'all') list = list.filter((m) => m.tier === tier)
    const col = COLS.find((c) => c.key === sortKey)
    if (col?.sort) {
      list.sort((a, b) => {
        const va = col.sort(a), vb = col.sort(b)
        const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
        return dir === 'asc' ? cmp : -cmp
      })
    }
    return list
  }, [data, q, tier, sortKey, dir])

  const onSort = (key) => {
    if (sortKey === key) setDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setDir('asc') }
  }

  return (
    <div className="rise">
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>Leaderboard</h1>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{data?.total ?? '…'} open models · 5-dimension scoring</span>
      </div>
      <p style={{ color: 'var(--muted)', margin: '0 0 18px' }}>
        Independent, zero paid placements. Click any column to sort.
      </p>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 14 }}>
        <input className="input" style={{ flex: 1, minWidth: 220 }} placeholder="Search models…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="select" value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="all">All tiers</option>
          {['S', 'A', 'B', 'C', 'D'].map((t) => <option key={t} value={t}>Tier {t}</option>)}
        </select>
      </div>

      <div className="glass" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              {COLS.map((c) => (
                <th key={c.key} className={c.cls} onClick={c.sort ? () => onSort(c.key) : undefined} style={c.sort ? { cursor: 'pointer' } : { cursor: 'default' }}>
                  {c.label}{sortKey === c.key && c.sort ? <span className="arrow">{dir === 'asc' ? '↑' : '↓'}</span> : null}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {!data && <tr><td colSpan={COLS.length} style={{ color: 'var(--muted)' }}>Loading leaderboard…</td></tr>}
            {data?.error && <tr><td colSpan={COLS.length} style={{ color: '#dc2626' }}>Error: {data.error}</td></tr>}
            {rows.map((m) => <ModelRow key={m.model_id} model={m} />)}
            {data && rows.length === 0 && <tr><td colSpan={COLS.length} style={{ color: 'var(--muted)' }}>No models match your filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
