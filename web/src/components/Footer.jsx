export default function Footer() {
  return (
    <footer style={{ position: 'relative', zIndex: 2, maxWidth: 1120, margin: '0 auto', padding: '26px 20px 40px' }}>
      <div style={{ borderTop: '1px solid var(--hair)', paddingTop: 20, display: 'flex', flexWrap: 'wrap', gap: 14, justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 14, height: 14, background: 'var(--accent)', borderRadius: 4, display: 'inline-block' }} />
          <span style={{ fontFamily: 'var(--display)', fontWeight: 700, fontSize: 15 }}>ModelRank</span>
          <span style={{ color: 'var(--muted)', fontSize: 13, marginLeft: 6 }}>Independent leaderboard for open models.</span>
        </div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
          <a href="https://github.com/rankmodel/rankmodel.github.io" target="_blank" rel="noreferrer" style={{ color: 'var(--muted)' }}>GitHub</a>
          <a href="./methodology" style={{ color: 'var(--muted)' }}>Methodology</a>
          <a href="./api" style={{ color: 'var(--muted)' }}>API</a>
          <a href="./pricing" style={{ color: 'var(--muted)' }}>Pricing</a>
        </div>
      </div>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--faint)', marginTop: 14, letterSpacing: '0.3px' }}>
        © {new Date().getFullYear()} MODELRANK · BUILT IN THE OPEN · ZERO PAID PLACEMENTS
      </div>
    </footer>
  )
}
