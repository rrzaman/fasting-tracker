import { useEffect, useState } from 'react'
import { createOverride, deleteOverride, fetchOverrides, updateOverride } from '../api'

// Mock data — replace with real API calls in Stage 2
const MOCK_LAST_UPLOAD = "2026-04-26"
const MOCK_RECIPIENTS = [
    { name: "Rayyan", number: "+1 (236) 990-6911" },
    { name: "Simrah", number: "+1 (825) 561-6921" },
]

function DataStatus() {
    const lastUpload = new Date(MOCK_LAST_UPLOAD)
    const today = new Date()
    const daysAgo = Math.floor((today - lastUpload) / (1000 * 60 * 60 * 24))

    const statusColor = daysAgo <= 7
        ? 'var(--emerald-light)'
        : daysAgo <= 14
            ? '#fcd34d'
            : '#f87171'

    const statusLabel = daysAgo <= 7
        ? 'Up to date'
        : daysAgo <= 14
            ? 'Getting stale'
            : 'Overdue — please upload'

    return (
        <div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>
                Health Data Status
            </h3>

            <div style={{
                background: 'var(--bg-secondary)',
                border: `1px solid ${statusColor}33`,
                borderRadius: '8px',
                padding: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem',
            }}>
                <div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                        Last uploaded
                    </p>
                    <p style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontFamily: 'var(--font-display)' }}>
                        {lastUpload.toLocaleDateString('en-CA', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '0.2rem' }}>
                        {daysAgo === 0 ? 'Today' : daysAgo === 1 ? 'Yesterday' : `${daysAgo} days ago`}
                    </p>
                </div>

                <div style={{ textAlign: 'right' }}>
                    <span style={{
                        background: `${statusColor}18`,
                        border: `1px solid ${statusColor}44`,
                        borderRadius: '20px',
                        color: statusColor,
                        fontSize: '0.78rem',
                        fontWeight: 500,
                        padding: '0.35rem 1rem',
                    }}>
                        {statusLabel}
                    </span>
                </div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: '0.75rem' }}>
                To update: export from Apple Health → place export.xml in data/ → run the ingestion pipeline
            </p>
        </div>
    )
}

function FastingOverrides() {
    const [selectedDate, setSelectedDate] = useState('')
    const [feedback, setFeedback] = useState(null)
    const [overrides, setOverrides] = useState({})

    useEffect(() => {
        async function loadOverrides() {
            try {
                const data = await fetchOverrides()
                const map = {}
                data.forEach(o => { map[o.date] = o.override_type === 'extra' })
                setOverrides(map)
            } catch (err) {
                console.error('Failed to load overrides:', err)
            }
        }
        loadOverrides()
    }, [])

    // Update handleOverride to call API:
    const handleOverride = async (date, didFast) => {
        try {
            const type = didFast ? 'extra' : 'skipped'
            if (overrides[date] !== undefined) {
                await updateOverride(date, type)
            } else {
                await createOverride(date, type)
            }
            setOverrides(prev => ({ ...prev, [date]: didFast }))
            setFeedback({ date, didFast })
            setTimeout(() => setFeedback(null), 3000)
        } catch (err) {
            console.error('Override failed:', err)
        }
    }

    // Update handleRemove:
    const handleRemove = async (date) => {
        try {
            await deleteOverride(date)
            setOverrides(prev => {
                const next = { ...prev }
                delete next[date]
                return next
            })
        } catch (err) {
            console.error('Delete failed:', err)
        }
    }

    const handleAdd = () => {
        if (!selectedDate) return
        if (overrides[selectedDate] !== undefined) return
        setOverrides(prev => ({ ...prev, [selectedDate]: true }))
        setSelectedDate('')
    }

    const sortedOverrides = Object.entries(overrides)
        .sort(([a], [b]) => b.localeCompare(a))

    // Filter to last 90 days for display
    const recentOverrides = sortedOverrides.filter(([date]) => {
        const d = new Date(date)
        const cutoff = new Date()
        cutoff.setDate(cutoff.getDate() - 90)
        return d >= cutoff
    })

    return (
        <div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Fasting Overrides
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
                Record days you fasted outside your regular schedule, or mark days you skipped.
            </p>

            {/* Add new override */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                <input
                    type="date"
                    value={selectedDate}
                    onChange={e => setSelectedDate(e.target.value)}
                    style={{
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border)',
                        borderRadius: '6px',
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-body)',
                        fontSize: '0.85rem',
                        padding: '0.4rem 0.75rem',
                        cursor: 'pointer',
                    }}
                />
                <button
                    onClick={() => { handleAdd(); handleOverride(selectedDate, true) }}
                    disabled={!selectedDate}
                    style={{
                        ...overrideBtnStyle,
                        background: selectedDate ? 'rgba(61,189,128,0.12)' : 'transparent',
                        border: `1px solid ${selectedDate ? 'var(--emerald)' : 'var(--border)'}`,
                        color: selectedDate ? 'var(--emerald-light)' : 'var(--text-muted)',
                        cursor: selectedDate ? 'pointer' : 'not-allowed',
                    }}
                >
                    + Extra fast
                </button>
                <button
                    onClick={() => { handleAdd(); handleOverride(selectedDate, false) }}
                    disabled={!selectedDate}
                    style={{
                        ...overrideBtnStyle,
                        background: selectedDate ? 'rgba(248,113,113,0.1)' : 'transparent',
                        border: `1px solid ${selectedDate ? '#f87171' : 'var(--border)'}`,
                        color: selectedDate ? '#f87171' : 'var(--text-muted)',
                        cursor: selectedDate ? 'pointer' : 'not-allowed',
                    }}
                >
                    ✕ Skipped fast
                </button>
            </div>

            {/* Feedback message */}
            {feedback && (
                <p style={{
                    color: feedback.didFast ? 'var(--emerald-light)' : '#f87171',
                    fontSize: '0.8rem',
                    marginBottom: '1rem',
                    transition: 'opacity 0.3s ease',
                }}>
                    {feedback.didFast
                        ? `✓ Recorded extra fast on ${feedback.date}`
                        : `✕ Marked ${feedback.date} as skipped`}
                </p>
            )}

            {/* Override list */}
            {recentOverrides.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    No overrides in the last 90 days.
                </p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {recentOverrides.map(([date, didFast]) => {
                        const d = new Date(date + 'T00:00:00')
                        return (
                            <div
                                key={date}
                                style={{
                                    alignItems: 'center',
                                    background: 'var(--bg-secondary)',
                                    border: `1px solid ${didFast ? 'rgba(61,189,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
                                    borderRadius: '6px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    padding: '0.6rem 1rem',
                                }}
                            >
                                <div>
                                    <span style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                                        {d.toLocaleDateString('en-CA', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                                    </span>
                                    <span style={{
                                        color: didFast ? 'var(--emerald-light)' : '#f87171',
                                        fontSize: '0.72rem',
                                        marginLeft: '0.75rem',
                                    }}>
                                        {didFast ? '✓ Extra fast' : '✕ Skipped'}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.4rem' }}>
                                    <button
                                        onClick={() => handleOverride(date, !didFast)}
                                        style={{ ...iconBtnStyle, color: 'var(--text-secondary)' }}
                                        title="Toggle"
                                    >
                                        ⇄
                                    </button>
                                    <button
                                        onClick={() => handleRemove(date)}
                                        style={{ ...iconBtnStyle, color: '#f87171' }}
                                        title="Remove"
                                    >
                                        ×
                                    </button>
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

function NotificationRecipients() {
    return (
        <div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Notification Recipients
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
                These numbers receive SMS reminders before upcoming fasting dates.
                To add or remove recipients, update your Lambda environment variables in AWS.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {MOCK_RECIPIENTS.map(({ name, number }) => (
                    <div
                        key={number}
                        style={{
                            alignItems: 'center',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border)',
                            borderRadius: '6px',
                            display: 'flex',
                            gap: '1rem',
                            padding: '0.6rem 1rem',
                        }}
                    >
                        <div style={{
                            alignItems: 'center',
                            background: 'rgba(61,189,128,0.12)',
                            border: '1px solid var(--emerald-muted)',
                            borderRadius: '50%',
                            color: 'var(--emerald-light)',
                            display: 'flex',
                            fontSize: '0.75rem',
                            fontWeight: 500,
                            height: '32px',
                            justifyContent: 'center',
                            minWidth: '32px',
                        }}>
                            {name[0]}
                        </div>
                        <div>
                            <p style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>{name}</p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{number}</p>
                        </div>
                        <span style={{
                            background: 'rgba(61,189,128,0.1)',
                            border: '1px solid var(--emerald-muted)',
                            borderRadius: '12px',
                            color: 'var(--emerald-light)',
                            fontSize: '0.65rem',
                            marginLeft: 'auto',
                            padding: '0.2rem 0.6rem',
                        }}>
                            Active
                        </span>
                    </div>
                ))}
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                Adding recipients currently requires AWS SNS sandbox verification.
                Streamlined recipient management is planned for a future update.
            </p>
        </div>
    )
}

// ── Main Settings component ──────────────────────────────────────────────────
export default function Settings() {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <DataStatus />
            <div style={{ height: '1px', background: 'var(--border)' }} />
            <FastingOverrides />
            <div style={{ height: '1px', background: 'var(--border)' }} />
            <NotificationRecipients />
        </div>
    )
}

const overrideBtnStyle = {
    borderRadius: '6px',
    fontFamily: 'var(--font-body)',
    fontSize: '0.8rem',
    padding: '0.4rem 0.9rem',
    transition: 'all 0.2s ease',
}

const iconBtnStyle = {
    background: 'none',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    padding: '0.2rem 0.4rem',
    transition: 'opacity 0.2s ease',
}