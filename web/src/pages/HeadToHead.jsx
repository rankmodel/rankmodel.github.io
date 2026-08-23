import { useEffect, useState } from 'react'
import { loadLeaderboard, DIMS, nameOf } from '../data.js'
import Radar from '../components/Radar.jsx'
import TierBadge from '../components/TierBadge.jsx'

export default function HeadToHead() {
  const [models, setModels] = useState(null)
  const [a, setA] = useState('')
  const [b, setB] = useState('')

  useEffect(() => {
    loadLeaderboard().then((d) => {
      setModels(d.models)
      setA(d.models[0]?.model_id || '')
      setB(d.models[1]?.model_id || '')
    }).catch(() => setModels([]))
  }, [])

  const ma = models?.find((m) => m.model_id === a)
  const mb = models?.find((m) => m.model_id === b)

  return (
    <div className="rise">
      <h1 className="section-title">Head to Head</h1>
      <p className="section-sub">Compare any two models across all five dimensions.</p>

      {!models && <p style={{ color: '#9aa3b8' }}>Loading…</p>}
      {models && (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 18 }}>
            <select className="select" value={a} onChange={(e) => setA(e.target.value)} style={{ flex: 1, minWidth: 200 }}>
              {models.map((m) => <option key={m.model_id} value={m.model_id}>{m.model_id}</option>)}
            </select>
            <span style={{ alignSelf: 'center', color: '#9aa3b8' }}>vs</span>
            <select className="select" value={b} onChange={(e) => setB(e.target.value)} style={{ flex: 1, minWidth: 200 }}>
              {models.map((m) => <option key={m.model_id} value={m.model_id}>{m.model_id}</option>)}
            </select>
          </div>

          {ma && mb && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {[ma, mb].map((m) => (
                <div key={m.model_id} className="glass" style={{ padding: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <TierBadge tier={m.tier} />
                    <div>
                      <div style={{ fontWeight: 700 }}>{nameOf(m.model_id)}</div>
                      <div style={{ color: '#9aa3b8', fontSize: 12 }}>#{m.rank}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', margin: '6px 0' }}>
                    <Radar breakdown={m.breakdown} size={200} />
                  </div>
                  <div style={{ fontSize: 30, fontWeight: 900, textAlign: 'center' }} className="grad-text">{m.composite.toFixed(1)}</div>
                  <div style={{ display: 'grid', gap: 6, marginTop: 10 }}>
                    {DIMS.map((d) => {
                      const v = m.breakdown?.[d.key] ?? 0
                      return (
                        <div key={d.key} style={{ fontSize: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9aa3b8' }}><span>{d.label}</span><span>{v.toFixed(1)}</span></div>
                          <div style={{ height: 6, borderRadius: 4, background: 'rgba(148,163,184,.15)', overflow: 'hidden', marginTop: 2 }}>
                            <div style={{ width: `${v}%`, height: '100%', background: 'linear-gradient(90deg,#6366f1,#a855f7)' }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
