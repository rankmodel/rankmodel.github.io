export default function Footer() {
  return (
    <footer style={{ position: 'relative', zIndex: 2, maxWidth: 1180, margin: '0 auto', padding: '28px 20px 40px', color: '#9aa3b8', fontSize: 13 }}>
      <div className="glass" style={{ padding: '22px 24px', display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 16, color: '#e6e9f2' }}>ModelRank</div>
          <div style={{ marginTop: 4 }}>The independent leaderboard for open HuggingFace models.</div>
          <div style={{ marginTop: 6 }}>5-dimension scoring · free badges · zero paid placements.</div>
        </div>
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
          <a href="https://github.com/rankmodel/rankmodel.github.io" target="_blank" rel="noreferrer">GitHub</a>
          <a href="./methodology">Methodology</a>
          <a href="./api">API</a>
          <a href="./pricing">Pricing</a>
        </div>
      </div>
      <div style={{ textAlign: 'center', marginTop: 16, opacity: 0.7 }}>
        © {new Date().getFullYear()} ModelRank · Built in the open.
      </div>
    </footer>
  )
}
