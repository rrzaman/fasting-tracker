export default function DemoBanner({ onExit }) {
    return (
        <div style={{
            background: 'rgba(61,189,128,0.1)',
            border: '1px solid var(--emerald-muted)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1.5rem',
            padding: '0.6rem 1rem',
        }}>
            <p style={{
                color: 'var(--emerald-light)',
                fontSize: '0.8rem',
                margin: 0,
            }}>
                ✦ Demo Mode — Synthetic data only. No real health information is displayed.
            </p>
            <button
                onClick={onExit}
                style={{
                    background: 'transparent',
                    border: '1px solid var(--emerald-muted)',
                    borderRadius: '6px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.75rem',
                    padding: '0.25rem 0.75rem',
                    transition: 'all 0.2s ease',
                    whiteSpace: 'nowrap',
                }}
            >
                Exit Demo
            </button>
        </div>
    )
}