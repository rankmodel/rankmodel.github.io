import { Link } from 'react-router-dom'

const DIMS = [
  { k: 'Benchmarks', d: 'Aggregated scores from MMLU-Pro, GPQA, HLE, GSM8K, and HumanEval, adjusted for model contamination.' },
  { k: 'Efficiency', d: 'Performance per parameter and per dollar. Rewards small, fast, cheap-to-run models.' },
  { k: 'Community', d: 'Downloads, likes, and ecosystem momentum on HuggingFace.' },
  { k: 'Recency', d: 'How current the weights and training data are. Fresh models score higher.' },
  { k: 'Reproducibility', d: 'Whether training data, code, and eval harness are openly published.' },
]

export default function Methodology() {
  return (
    <div className="rise">
      <h1 className="section-title">Methodology</h1>
      <p className="section-sub">How ModelRank scores open models, and why it stays independent.</p>

      <section className="glass" style={{ padding: 24, marginBottom: 18 }}>
        <h2 style={{ marginTop: 0 }}>The 5 dimensions</h2>
        <p style={{ color: '#9aa3b8' }}>Every model gets a composite from five normalized dimensions, each scored 0–100.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 14 }}>
          {DIMS.map((x) => (
            <div key={x.k} className="glass" style={{ padding: 16, background: 'rgba(15,15,35,.4)' }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }} className="grad-text">{x.k}</div>
              <div style={{ color: '#9aa3b8', fontSize: 14 }}>{x.d}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="glass" style={{ padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>Independence, by design</h2>
        <ul style={{ color: '#cbd5e1', lineHeight: 1.8, paddingLeft: 18 }}>
          <li><strong>Zero paid placements.</strong> No model can buy a higher rank. Ever.</li>
          <li><strong>Open scoring.</strong> Every weight and formula is published; raw rankings ship as CSV.</li>
          <li><strong>Free badges.</strong> Embeddable SVG badges for any ranked model, no account needed.</li>
          <li><strong>Reproducible.</strong> Scores are recomputed daily from public HuggingFace metadata.</li>
        </ul>
        <p style={{ color: '#9aa3b8', marginTop: 12 }}>
          Questions or want your model evaluated? <Link to="/api" style={{ color: '#a5b4fc' }}>See the API</Link> or open an issue on GitHub.
        </p>
      </section>
    </div>
  )
}
