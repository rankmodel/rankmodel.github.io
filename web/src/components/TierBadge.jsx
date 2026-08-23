export default function TierBadge({ tier, size = 'md' }) {
  const map = {
    S: { bg: '#f3e8ff', fg: '#7c3aed', bd: '#e9d5ff' },
    A: { bg: '#eef0fe', fg: '#4f46e5', bd: '#dfe1fb' },
    B: { bg: '#e0f7fb', fg: '#0e7490', bd: '#cff3f9' },
    C: { bg: '#e7f7ef', fg: '#047857', bd: '#d3f0e0' },
    D: { bg: '#fef3e2', fg: '#b45309', bd: '#fde9c8' },
  }
  const c = map[tier] || { bg: '#eef0f4', fg: '#6b7280', bd: '#e2e5ea' }
  const px = size === 'sm' ? 20 : 24
  return (
    <span title={`Tier ${tier}`}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        minWidth: px, height: px, padding: '0 7px', borderRadius: 7,
        fontSize: size === 'sm' ? 11 : 12.5, fontWeight: 700,
        background: c.bg, color: c.fg, border: `1px solid ${c.bd}`,
      }}>
      {tier}
    </span>
  )
}
