export const DIMS = [
  { key: 'benchmarks', label: 'Benchmarks' },
  { key: 'efficiency', label: 'Efficiency' },
  { key: 'community', label: 'Community' },
  { key: 'recency', label: 'Recency' },
  { key: 'reproducibility', label: 'Reproducibility' },
]

export const TIER_COLORS = {
  S: '#a855f7',
  A: '#6366f1',
  B: '#22d3ee',
  C: '#34d399',
  D: '#f59e0b',
}

export async function loadLeaderboard() {
  const res = await fetch('./leaderboard.json')
  if (!res.ok) throw new Error('Failed to load leaderboard.json')
  const data = await res.json()
  const models = Array.isArray(data.models) ? data.models : Object.values(data.models || {})
  return { updatedAt: data.updated_at, total: data.total ?? models.length, models }
}

export function tierColor(tier) {
  return TIER_COLORS[tier] || '#64748b'
}

export function orgOf(modelId) {
  return modelId.split('/')[0]
}
export function nameOf(modelId) {
  return modelId.split('/').slice(1).join('/')
}
