export default function Footer() {
  return (
    <footer style={{ position: 'relative', zIndex: 2, maxWidth: 1140, margin: '0 auto', padding: '28px 20px 40px', color: 'var(--muted)', fontSize: 13 }}>
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 22, display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text)' }}>ModelRank</div>
          <div style={{ marginTop: 4 }}>The independent leaderboard for open HuggingFace models.</div>
        </div>
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
          <a href="https://github.com/rankmodel/rankmodel.github.io" target="_blank" rel="noreferrer">GitHub</a>
          <a href="./methodology">Methodology</a>
          <a href="./api">API</a>
          <a href="./pricing">Pricing</a>
        </div>
      </div>
      <div style={{ textAlign: 'center', marginTop: 16, color: 'var(--faint)' }}>
        © {new Date().getFullYear()} ModelRank · Built in the open.
      </div>
    </footer>
  )
}
