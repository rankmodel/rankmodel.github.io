import { Link } from 'react-router-dom'
import TierBadge from './TierBadge.jsx'
import { nameOf, orgOf } from '../data.js'

function Cell({ value }) {
  return (
    <td className="num">
      <div style={{ fontWeight: 600 }}>{typeof value === 'number' ? value.toFixed(1) : value}</div>
      <div className="minibar"><span style={{ width: `${value}%` }} /></div>
    </td>
  )
}

export default function ModelRow({ model }) {
  const b = model.breakdown || {}
  return (
    <tr>
      <td className="num" style={{ color: 'var(--muted)', fontWeight: 600, whiteSpace: 'nowrap' }}>#{model.rank}</td>
      <td>
        <Link to={`/model/${encodeURIComponent(model.model_id)}`} style={{ fontWeight: 600, color: 'var(--ink)' }}>
          {nameOf(model.model_id)}
        </Link>
        <div style={{ fontSize: 12.5, color: 'var(--faint)' }}>{orgOf(model.model_id)}</div>
      </td>
      <td style={{ textAlign: 'center' }}><TierBadge tier={model.tier} /></td>
      <td className="num" style={{ fontWeight: 700, color: 'var(--accent-ink)', fontSize: 15 }}>{model.composite.toFixed(1)}</td>
      <Cell value={b.benchmarks} />
      <Cell value={b.efficiency} />
      <Cell value={b.community} />
      <td className="num hide-sm" style={{ color: 'var(--muted)' }}>{b.recency?.toFixed(0)}</td>
      <td className="num hide-sm" style={{ color: 'var(--muted)' }}>{b.reproducibility?.toFixed(0)}</td>
      <td className="hide-sm">
        <a href={model.badge_url} target="_blank" rel="noreferrer">
          <img src={model.badge_url} alt="badge" height="20" />
        </a>
      </td>
    </tr>
  )
}
