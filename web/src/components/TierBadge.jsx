import { Link } from 'react-router-dom'

export default function TierBadge({ tier, size = 'md' }) {
  const colors = {
    S: '#a855f7', A: '#6366f1', B: '#22d3ee', C: '#34d399', D: '#f59e0b',
  }
  const c = colors[tier] || '#64748b'
  const px = size === 'sm' ? 18 : 22
  return (
    <span
      title={`Tier ${tier}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: px, height: px,
        borderRadius: '50%',
        fontSize: size === 'sm' ? 11 : 13,
        fontWeight: 800,
        color: '#0b0b18',
        background: c,
        boxShadow: `0 0 0 3px ${c}33`,
      }}
    >
      {tier}
    </span>
  )
}
