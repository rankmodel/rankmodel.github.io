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

// Progressive loading: the frontend fetches one page at a time so the initial
// payload is small. Pages live at ./pages/page-N.json (generated at build time).
export const PAGE_SIZE = 100

export async function loadPage(n) {
  const res = await fetch(`./pages/page-${n}.json`)
  if (!res.ok) throw new Error(`Failed to load page ${n}`)
  const data = await res.json()
  const models = Array.isArray(data.models) ? data.models : []
  return {
    updatedAt: data.updated_at,
    total: data.total ?? models.length,
    page: data.page ?? n,
    totalPages: data.total_pages ?? 1,
    models,
  }
}

export async function loadAllPages() {
  const first = await loadPage(1)
  const rest = await Promise.all(
    Array.from({ length: first.totalPages - 1 }, (_, i) => loadPage(i + 2).then((d) => d.models)),
  )
  return {
    updatedAt: first.updatedAt,
    total: first.total,
    models: [...first.models, ...rest.flat()],
  }
}
