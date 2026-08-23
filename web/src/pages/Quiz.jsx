import { useEffect, useMemo, useState } from 'react'
import { loadLeaderboard } from '../data.js'
import { Link } from 'react-router-dom'

const QUESTIONS = [
  { id: 'useCase', q: 'What will you mostly do?', opts: [['coding', 'Coding'], ['chat', 'Chat / assistant'], ['reasoning', 'Hard reasoning'], ['local', 'Run locally']] },
  { id: 'hardware', q: 'Your hardware?', opts: [['potato', 'Laptop / CPU'], ['gpu', 'Single GPU'], ['datacenter', 'Datacenter']] },
  { id: 'priority', q: 'What matters most?', opts: [['speed', 'Speed / efficiency'], ['power', 'Raw power'], ['open', 'Openness']] },
]

export default function Quiz() {
  const [data, setData] = useState(null)
  const [sel, setSel] = useState({})
  const [done, setDone] = useState(false)

  useEffect(() => { loadLeaderboard().then((d) => setData(d.models)).catch(() => setData([])) }, [])

  const recs = useMemo(() => {
    if (!data || !done) return []
    return [...data]
      .map((m) => {
        const b = m.breakdown || {}
        let s = 0
        if (sel.priority === 'speed') s += b.efficiency
        if (sel.priority === 'power') s += b.benchmarks
        if (sel.priority === 'open') s += b.reproducibility
        if (sel.hardware === 'potato') s += b.efficiency * 1.5
        if (sel.hardware === 'datacenter') s += b.benchmarks
        if (sel.useCase === 'local') s += b.efficiency
        if (sel.useCase === 'reasoning') s += b.benchmarks
        return { m, s }
      })
      .sort((a, b) => b.s - a.s)
      .slice(0, 3)
      .map((x) => x.m)
  }, [data, sel, done])

  const answer = (id, v) => {
    const next = { ...sel, [id]: v }
    setSel(next)
    if (QUESTIONS.every((qq) => next[qq.id])) setDone(true)
  }

  return (
    <div className="rise">
      <h1 className="section-title">Find your model</h1>
      <p className="section-sub">Three questions. We rank the leaderboard to your needs.</p>

      <section className="glass" style={{ padding: 24 }}>
        {QUESTIONS.map((qq) => (
          <div key={qq.id} style={{ marginBottom: 18 }}>
            <div style={{ fontWeight: 700, marginBottom: 10 }}>{qq.q}</div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {qq.opts.map(([v, label]) => (
                <button key={v} className={sel[qq.id] === v ? 'btn btn-primary' : 'btn btn-ghost'} onClick={() => answer(qq.id, v)} style={{ padding: '9px 16px', fontSize: 14 }}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        ))}

        {done && (
          <div className="rise">
            <h2 style={{ fontSize: 20 }}>Your top picks</h2>
            <div style={{ display: 'grid', gap: 10 }}>
              {recs.map((m) => (
                <Link key={m.model_id} to={`/model/${encodeURIComponent(m.model_id)}`} className="glass" style={{ padding: 14, display: 'block', background: 'var(--bg-soft)' }}>
                  <span style={{ fontWeight: 700 }}>{m.model_id}</span> <span style={{ color: '#9aa3b8' }}>· {m.composite.toFixed(1)} · {m.tier}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
