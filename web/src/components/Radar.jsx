import { DIMS } from '../data.js'

// Lightweight SVG radar for the 5 scoring dimensions.
export default function Radar({ breakdown, size = 220 }) {
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 28
  const n = DIMS.length
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2
  const point = (i, val) => {
    const rad = (val / 100) * r
    return [cx + Math.cos(angle(i)) * rad, cy + Math.sin(angle(i)) * rad]
  }
  const poly = DIMS.map((d, i) => point(i, breakdown[d.key] ?? 0).join(',')).join(' ')
  const rings = [0.25, 0.5, 0.75, 1]
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Score breakdown radar">
      {rings.map((rr, idx) => (
        <polygon
          key={idx}
          points={DIMS.map((_, i) => {
            const rad = rr * r
            return `${cx + Math.cos(angle(i)) * rad},${cy + Math.sin(angle(i)) * rad}`
          }).join(' ')}
          fill="none"
          stroke="rgba(148,163,184,0.18)"
          strokeWidth="1"
        />
      ))}
      {DIMS.map((d, i) => {
        const [x, y] = point(i, 100)
        return <line key={d.key} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
      })}
      <polygon points={poly} fill="rgba(129,140,248,0.35)" stroke="#a855f7" strokeWidth="2" />
      {DIMS.map((d, i) => {
        const [x, y] = point(i, breakdown[d.key] ?? 0)
        return <circle key={d.key} cx={x} cy={y} r="3.2" fill="#a855f7" />
      })}
      {DIMS.map((d, i) => {
        const [x, y] = point(i, 118)
        return (
          <text key={d.key} x={x} y={y} fontSize="11" fill="#9aa3b8" textAnchor="middle" dominantBaseline="middle">
            {d.label.slice(0, 4)}
          </text>
        )
      })}
    </svg>
  )
}
