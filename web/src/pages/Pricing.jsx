const TIERS = [
  {
    name: 'Free Forever', price: '$0', tag: 'For everyone',
    feats: ['Unlimited model lookups', 'Free embeddable SVG badges', 'Full CSV rankings', 'Community support'],
    primary: true,
  },
  {
    name: 'Pro', price: 'Custom', tag: 'For teams',
    feats: ['High-volume API access', 'Custom scoring weight profiles', 'Branded leaderboards', 'Priority eval queue'],
    primary: false,
  },
  {
    name: 'Enterprise', price: 'Talk to us', tag: 'For orgs',
    feats: ['Self-hosted scoring', 'Private model evaluation', 'SLA + support', 'Bespoke dimensions'],
    primary: false,
  },
]

export default function Pricing() {
  return (
    <div className="rise">
      <h1 className="section-title">Pricing</h1>
      <p className="section-sub">ModelRank's rankings are free and never pay-to-win. Paid tiers are for access, not rank.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 16 }}>
        {TIERS.map((t) => (
          <div key={t.name} className="glass" style={{ padding: 24, borderColor: t.primary ? 'rgba(129,140,248,.55)' : 'var(--border)', boxShadow: t.primary ? '0 18px 48px rgba(99,102,241,.3)' : 'var(--shadow)' }}>
            <div className="pill" style={{ marginBottom: 12 }}>{t.tag}</div>
            <h2 style={{ margin: '0 0 4px' }}>{t.name}</h2>
            <div style={{ fontSize: 34, fontWeight: 900 }} className="grad-text">{t.price}</div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '16px 0', color: '#cbd5e1', lineHeight: 2 }}>
              {t.feats.map((f) => <li key={f}>✓ {f}</li>)}
            </ul>
            <a className={t.primary ? 'btn btn-primary' : 'btn btn-ghost'} href="https://github.com/rankmodel/rankmodel.github.io" style={{ width: '100%', textAlign: 'center' }}>
              {t.primary ? 'Get started' : 'Contact us'}
            </a>
          </div>
        ))}
      </div>

      <p style={{ color: '#9aa3b8', marginTop: 20, textAlign: 'center' }}>
        Rankings are identical for every plan. You can't pay to rank higher.
      </p>
    </div>
  )
}
