export default function TierBadge({ tier, size = 'md' }) {
  const map = {
    S: { bg: '#f3eafa', fg: '#6d28d9', bd: '#e6d6f5' },
    A: { bg: '#e8eefe', fg: '#1d4ed8', bd: '#d3e0fb' },
    B: { bg: '#e3f4fd', fg: '#0369a1', bd: '#cce9f8' },
    C: { bg: '#e4f7ee', fg: '#047857', bd: '#cdeede' },
    D: { bg: '#fdf3df', fg: '#b45309', bd: '#f6e6c2' },
  }
  const c = map[tier] || { bg: '#f0efec', fg: '#6f6f78', bd: '#e3e1dc' }
  const px = size === 'sm' ? 20 : 23
  return (
    <span title={`Tier ${tier}`}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        minWidth: px, height: px, padding: '0 6px', borderRadius: 6,
        fontSize: size === 'sm' ? 11 : 12, fontWeight: 700, fontFamily: 'var(--mono)',
        background: c.bg, color: c.fg, border: `1px solid ${c.bd}`,
      }}>
      {tier}
    </span>
  )
}
