import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadPage, loadAllPages } from '../data.js'
import ModelRow from '../components/ModelCard.jsx'

const COLS = [
  { key: 'rank', label: 'Rank', sort: (m) => m.rank, num: true },
  { key: 'model', label: 'Model', sort: (m) => m.model_id.toLowerCase() },
  { key: 'tier', label: 'Tier', sort: (m) => m.tier },
  { key: 'composite', label: 'Composite', sort: (m) => m.composite, num: true },
  { key: 'benchmarks', label: 'Bench', sort: (m) => m.breakdown?.benchmarks ?? 0, num: true },
  { key: 'efficiency', label: 'Effic', sort: (m) => m.breakdown?.efficiency ?? 0, num: true },
  { key: 'community', label: 'Comm', sort: (m) => m.breakdown?.community ?? 0, num: true },
  { key: 'recency', label: 'Recency', sort: (m) => m.breakdown?.recency ?? 0, num: true, cls: 'hide-sm' },
  { key: 'reproducibility', label: 'Repro', sort: (m) => m.breakdown?.reproducibility ?? 0, num: true, cls: 'hide-sm' },
  { key: 'badge', label: 'Badge', sort: null, cls: 'hide-sm' },
]

const STEP = 10 // rows revealed per "Read more"

function Stat({ value, label, accent, last }) {
  return (
    <div style={{ flex: '1 1 150px', padding: '14px 18px 14px 0', borderRight: last ? 'none' : '1px solid var(--hair)' }}>
      <div className="mono" style={{ fontSize: 26, fontWeight: 600, color: accent ? 'var(--accent)' : 'var(--ink)', letterSpacing: '-0.5px' }}>{value}</div>
      <div style={{ fontSize: 11.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
    </div>
  )
}

export default function Leaderboard() {
  const [status, setStatus] = useState('loading') // loading | ok | error
  const [error, setError] = useState(null)
  const [loaded, setLoaded] = useState([])          // models fetched so far
  const [meta, setMeta] = useState({ total: 0, totalPages: 0, updatedAt: null })
  const [visible, setVisible] = useState(STEP)
  const [loadingMore, setLoadingMore] = useState(false)
  const [allLoaded, setAllLoaded] = useState(false)

  const [q, setQ] = useState('')
  const [tier, setTier] = useState('all')
  const [sortKey, setSortKey] = useState('rank')
  const [dir, setDir] = useState('asc')

  const loadedRef = useRef([])
  const nextPageRef = useRef(1)
  const metaRef = useRef(meta)
  useEffect(() => { loadedRef.current = loaded }, [loaded])
  useEffect(() => { metaRef.current = meta }, [meta])

  // Initial load: only page 1 (~35KB) is fetched.
  useEffect(() => {
    let cancelled = false
    loadPage(1)
      .then((d) => {
        if (cancelled) return
        loadedRef.current = d.models
        nextPageRef.current = 2
        setLoaded(d.models)
        setMeta({ total: d.total, totalPages: d.totalPages, updatedAt: d.updatedAt })
        setStatus('ok')
      })
      .catch((e) => { if (!cancelled) { setError(e.message); setStatus('error') } })
    return () => { cancelled = true }
  }, [])

  const appendPage = useCallback(async () => {
    const n = nextPageRef.current
    if (n > metaRef.current.totalPages) return false
    const d = await loadPage(n)
    nextPageRef.current = n + 1
    const next = loadedRef.current.concat(d.models)
    loadedRef.current = next
    setLoaded(next)
    return true
  }, [])

  // Collapse the revealed count back to 10 whenever the view changes.
  useEffect(() => { setVisible(STEP) }, [q, tier, sortKey, dir])

  const rows = useMemo(() => {
    let list = loaded.slice()
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
  }, [loaded, q, tier, sortKey, dir])

  const shown = rows.slice(0, visible)
  const hidden = Math.max(0, rows.length - visible)

  const onSort = (key) => {
    if (sortKey === key) setDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setDir('asc') }
  }

  const onReadMore = async () => {
    // If we've revealed everything we've fetched, pull the next page first.
    if (loadedRef.current.length < visible + STEP && nextPageRef.current <= metaRef.current.totalPages) {
      setLoadingMore(true)
      try { await appendPage() } finally { setLoadingMore(false) }
    }
    setVisible((v) => v + STEP)
  }

  const onLoadAll = async () => {
    setLoadingMore(true)
    try {
      const all = await loadAllPages()
      loadedRef.current = all.models
      nextPageRef.current = all.totalPages + 1
      setLoaded(all.models)
      setMeta((m) => ({ ...m, total: all.total }))
      setAllLoaded(true)
    } finally { setLoadingMore(false) }
  }

  const filtering = q.trim() !== '' || tier !== 'all'
  const notFullyLoaded = !allLoaded && loaded.length < meta.total

  return (
    <div className="rise" id="main-content">
      <header style={{ marginBottom: 22 }}>
        <div className="eyebrow">Independent leaderboard · open HuggingFace models</div>
        <h1 style={{ fontFamily: 'var(--display)', fontWeight: 700, fontSize: 'clamp(26px,5vw,40px)', letterSpacing: '-1px', margin: '8px 0 6px', lineHeight: 1.05 }}>
          Rank the open web's models. Honestly.
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: 16, maxWidth: 640, margin: '0 0 18px', lineHeight: 1.55 }}>
          A five-dimension composite score, free embeddable badges, and zero paid placements. Click any column to sort.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', borderTop: '1px solid var(--hair)', borderBottom: '1px solid var(--hair)' }}>
          <Stat value={meta.total || (status === 'loading' ? '—' : '0')} label="models ranked" />
          <Stat value="5" label="scoring dimensions" />
          <Stat value="0" label="paid placements" accent last />
        </div>
      </header>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 14 }}>
        <input
          className="input"
          style={{ flex: 1, minWidth: 220 }}
          placeholder="Search models…"
          aria-label="Search models by name"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="select" aria-label="Filter by tier" value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="all">All tiers</option>
          {['S', 'A', 'B', 'C', 'D'].map((t) => <option key={t} value={t}>Tier {t}</option>)}
        </select>
      </div>

      <div className="glass" style={{ overflowX: 'auto' }}>
        <table className="table" aria-label="ModelRank leaderboard" aria-busy={status === 'loading'}>
          <caption className="sr-only">
            ModelRank leaderboard of {meta.total || 'open AI'} models, sortable by column. Use the Read more button to reveal additional rows.
          </caption>
          <thead>
            <tr>
              {COLS.map((c) => {
                const sortable = !!c.sort
                const inner = (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    {c.label}
                    {sortable && sortKey === c.key ? <span className="arrow">{dir === 'asc' ? '↑' : '↓'}</span> : null}
                  </span>
                )
                return (
                  <th
                    key={c.key}
                    scope="col"
                    className={(c.num ? 'num ' : '') + (c.cls || '')}
                    aria-sort={sortable ? (sortKey === c.key ? (dir === 'asc' ? 'ascending' : 'descending') : 'none') : undefined}
                  >
                    {sortable ? (
                      <button
                        type="button"
                        className="th-sort"
                        onClick={() => onSort(c.key)}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSort(c.key) } }}
                      >
                        {inner}
                      </button>
                    ) : inner}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {status === 'loading' && Array.from({ length: STEP }).map((_, i) => (
              <tr key={`sk-${i}`}><td colSpan={COLS.length}><div className="skeleton" style={{ height: 16 }} /></td></tr>
            ))}
            {status === 'error' && <tr><td colSpan={COLS.length} style={{ color: '#c0392b' }}>Error: {error}</td></tr>}
            {status === 'ok' && shown.map((m) => <ModelRow key={m.model_id} model={m} />)}
            {status === 'ok' && rows.length === 0 && <tr><td colSpan={COLS.length} style={{ color: 'var(--muted)' }}>No models match your filters.</td></tr>}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginTop: 14, flexWrap: 'wrap' }}>
        <div className="mono" style={{ fontSize: 12.5, color: 'var(--muted)' }} aria-live="polite">
          {filtering && notFullyLoaded
            ? `Searching ${loaded.length} of ${meta.total} loaded models`
            : `Showing ${Math.min(visible, rows.length)} of ${rows.length} models`}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {filtering && notFullyLoaded && (
            <button type="button" className="select" style={{ cursor: 'pointer' }} onClick={onLoadAll} disabled={loadingMore}>
              {loadingMore ? 'Loading…' : `Load all ${meta.total} models`}
            </button>
          )}
          {hidden > 0 && (
            <button
              type="button"
              className="select"
              style={{ cursor: 'pointer' }}
              aria-label={`Load ${Math.min(STEP, hidden)} more models`}
              onClick={onReadMore}
              disabled={loadingMore}
            >
              {loadingMore ? 'Loading…' : `Read more (${hidden} hidden)`}
            </button>
          )}
          {visible > STEP && (
            <button type="button" className="select" style={{ cursor: 'pointer' }} onClick={() => setVisible(STEP)}>
              Show less
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
