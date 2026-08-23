import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error) {
    return { error }
  }
  componentDidCatch(error, info) {
    console.error('ModelRank render error:', error, info)
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ maxWidth: 640, margin: '12vh auto', padding: 24, fontFamily: 'var(--font)' }}>
          <div style={{ width: 18, height: 18, background: 'var(--accent)', borderRadius: 5, marginBottom: 14 }} />
          <h1 style={{ fontFamily: 'var(--display)', fontSize: 24, margin: '0 0 8px' }}>Something went wrong</h1>
          <p style={{ color: 'var(--muted)' }}>A part of the page failed to render. Try refreshing, or open an issue on GitHub.</p>
          <pre style={{ background: '#f3f2ef', border: '1px solid var(--hair)', borderRadius: 8, padding: 12, overflow: 'auto', fontSize: 12, color: '#9a2f17' }}>
            {String(this.state.error && this.state.error.stack || this.state.error)}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}
