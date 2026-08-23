import { Link } from 'react-router-dom'
import TierBadge from './TierBadge.jsx'
import { nameOf, orgOf } from '../data.js'

export default function ModelCard({ model, index }) {
  const dims = model.breakdown || {}
  return (
    <Link to={`/model/${encodeURIComponent(model.model_id)}`} className="glass" style={{ display: 'block', padding: 18, transition: 'transform .22s cubic-bezier(.2,.8,.2,1), border-color .22s', textDecoration: 'none' }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-6px)'; e.currentTarget.style.borderColor = 'rgba(129,140,248,.6)'; e.currentTarget.style.boxShadow = '0 18px 48px rgba(99,102,241,.3)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = ''; e.currentTarget.style.borderColor = ''; e.currentTarget.style.boxShadow = '' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 15, fontWeight: 800, color: '#94a3b8', width: 28 }}>#{model.rank}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 16, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{nameOf(model.model_id)}</div>
          <div style={{ fontSize: 12, color: '#9aa3b8' }}>{orgOf(model.model_id)}</div>
        </div>
        <TierBadge tier={model.tier} />
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, margin: '12px 0 10px' }}>
        <span style={{ fontSize: 26, fontWeight: 900 }} className="grad-text">{model.composite.toFixed(1)}</span>
        <span style={{ fontSize: 12, color: '#9aa3b8' }}>composite</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 14px' }}>
        {Object.entries(dims).map(([k, v]) => (
          <div key={k} style={{ fontSize: 11 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9aa3b8', textTransform: 'capitalize' }}>
              <span>{k}</span><span>{typeof v === 'number' ? v.toFixed(0) : v}</span>
            </div>
            <div style={{ height: 5, borderRadius: 4, background: 'rgba(148,163,184,.15)', overflow: 'hidden', marginTop: 3 }}>
              <div style={{ width: `${v}%`, height: '100%', background: 'linear-gradient(90deg,#6366f1,#a855f7)' }} />
            </div>
          </div>
        ))}
      </div>
    </Link>
  )
}
