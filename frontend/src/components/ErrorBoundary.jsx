import { Component } from 'react'

// Error boundaries must be class components — React provides no hook equivalent
// for componentDidCatch / getDerivedStateFromError as of React 18.
class ErrorBoundary extends Component {
  state = { hasError: false, error: null }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught an error:', error, info)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children

    const { tabName } = this.props
    const { error } = this.state

    return (
      <div className="card card--error" style={{ textAlign: 'center', padding: '3rem' }}>
        <h2 style={{ color: 'var(--prohibited)', marginBottom: '0.75rem' }}>
          Something went wrong
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          {tabName
            ? `The ${tabName} view ran into an unexpected error.`
            : 'This view ran into an unexpected error.'}
        </p>
        {error?.message && (
          <p style={{
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            fontFamily: 'monospace',
            marginBottom: '1.5rem',
            wordBreak: 'break-word',
          }}>
            {error.message}
          </p>
        )}
        <button
          onClick={this.handleReload}
          style={{
            background: 'rgba(240,192,64,0.1)',
            border: '1px solid var(--gold)',
            borderRadius: '8px',
            color: 'var(--gold)',
            cursor: 'pointer',
            fontFamily: 'var(--font-body)',
            fontSize: '0.9rem',
            padding: '0.75rem 2rem',
            transition: 'all 0.2s ease',
          }}
        >
          Reload
        </button>
      </div>
    )
  }
}

export default ErrorBoundary
