import { useEffect, useState } from 'react'
import { createOverride, deleteOverride, fetchSystemStatus, updateOverride } from '../api'

function DataStatus({ healthData }) {
    // Dynamically calculate the last upload date from the health dataset
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]
    const maxDateStr = healthData?.length
        ? healthData.map(d => d.date).filter(d => d <= todayStr).sort().pop()
        : null

    if (!maxDateStr) return (
        <div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>
                Health Data Status
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No health data uploaded yet.
            </p>
        </div>
    )

    const lastUpload = new Date(maxDateStr + "T00:00:00")
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

function FastingOverrides({ isDemoMode, token, overrides, onOverridesChange, fastingData }) {
    const [selectedDate, setSelectedDate] = useState('')
    const [feedback, setFeedback] = useState(null)
    const isAlreadyFasting = selectedDate && fastingData?.[selectedDate]?.is_fasting

    // Update handleOverride to call API:
    const handleOverride = async (date, didFast) => {

        if (!isDemoMode) {
            try {
                const type = didFast ? 'extra' : 'skipped'
                if (overrides[date] !== undefined) {
                    await updateOverride(token, date, type)
                } else {
                    await createOverride(token, date, type)
                }
            } catch (err) {
                return
            }
        }
        onOverridesChange(prev => ({ ...prev, [date]: didFast }))
        setFeedback({ date, didFast })
        setTimeout(() => setFeedback(null), 3000)
    }

    // Update handleRemove:
    const handleRemove = async (date) => {
        if (!isDemoMode) {
            try {
                await deleteOverride(token, date)
            } catch (err) {
                return
            }
        }
        onOverridesChange(prev => {
            const next = { ...prev }
            delete next[date]
            return next
        })
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
                {isDemoMode && (
                    <span style={{
                        color: 'var(--emerald-light)',
                        fontSize: '0.65rem',
                        marginLeft: '0.5rem',
                        opacity: 0.7,
                    }}>
                        (demo — changes not saved)
                    </span>
                )}
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
                    onClick={() => {
                        if (!selectedDate) return
                        handleOverride(selectedDate, true)
                        setSelectedDate('')
                    }}
                    disabled={!selectedDate || isAlreadyFasting}
                    style={{
                        ...overrideBtnStyle,
                        background: selectedDate && !isAlreadyFasting ? 'rgba(61,189,128,0.12)' : 'transparent',
                        border: `1px solid ${selectedDate && !isAlreadyFasting ? 'var(--emerald)' : 'var(--border)'}`,
                        color: selectedDate && !isAlreadyFasting ? 'var(--emerald-light)' : 'var(--text-muted)',
                        cursor: selectedDate && !isAlreadyFasting ? 'pointer' : 'not-allowed',
                    }}
                >
                    + Extra fast
                </button>
                <button
                    onClick={() => {
                        if (!selectedDate) return
                        handleOverride(selectedDate, false)
                        setSelectedDate('')
                    }}
                    disabled={!selectedDate || !isAlreadyFasting}
                    style={{
                        ...overrideBtnStyle,
                        background: selectedDate && isAlreadyFasting ? 'rgba(248,113,113,0.1)' : 'transparent',
                        border: `1px solid ${selectedDate && isAlreadyFasting ? '#f87171' : 'var(--border)'}`,
                        color: selectedDate && isAlreadyFasting ? '#f87171' : 'var(--text-muted)',
                        cursor: selectedDate && isAlreadyFasting ? 'pointer' : 'not-allowed',
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

function NotificationRecipients({ onSignOut, isDemoMode }) {
    const [recipients, setRecipients] = useState([])
    const [isExpanded, setIsExpanded] = useState(false)
    const MAX_VISIBLE = 2

    useEffect(() => {
        if (isDemoMode) {
            setRecipients([{ name: "Rayyan" }, { name: "Simrah" }])
            return
        }
        fetchSystemStatus()
            .then(data => setRecipients(data.recipients || []))
            .catch(console.error)
    }, [isDemoMode])

    const visibleRecipients = isExpanded ? RECIPIENTS : RECIPIENTS.slice(0, MAX_VISIBLE)
    const hiddenCount = RECIPIENTS.length - MAX_VISIBLE

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>
                    Notification Recipients
                </h3>
                <span style={{
                    background: 'rgba(61,189,128,0.1)',
                    border: '1px solid var(--emerald-muted)',
                    borderRadius: '12px',
                    color: 'var(--emerald-light)',
                    fontSize: '0.75rem',
                    padding: '0.2rem 0.6rem',
                    fontWeight: 500,
                }}>
                    🟢 {RECIPIENTS.length} Active
                </span>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
                These individuals receive SMS reminders before upcoming fasting dates.
                To add or remove recipients, update your Lambda environment variables in AWS.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {visibleRecipients.map(({ name }) => (
                    <div
                        key={name}
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
                        </div>
                        <span style={{
                            color: 'var(--emerald-light)',
                            fontSize: '1rem',
                            marginLeft: 'auto',
                        }}>
                            ✓
                        </span>
                    </div>
                ))}

                {hiddenCount > 0 && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={{
                            background: 'transparent',
                            border: '1px dashed var(--border)',
                            borderRadius: '6px',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            padding: '0.6rem 1rem',
                            textAlign: 'center',
                            transition: 'all 0.2s ease',
                            marginTop: '0.25rem'
                        }}
                    >
                        {isExpanded ? 'Show less' : `+ ${hiddenCount} more family members`}
                    </button>
                )}
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                Adding recipients currently requires AWS SNS sandbox verification.
                Streamlined recipient management is planned for a future update.
            </p>
            <button
                onClick={onSignOut}
                style={{
                    background: 'transparent',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.75rem',
                    padding: '0.3rem 0.8rem',
                }}
            >
                Sign out
            </button>
        </div>
    )
}

function SystemStatus({ isDemoMode }) {
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (isDemoMode) {
            setStatus({
                last_reminder_run: {
                    timestamp: new Date().toISOString(),
                    status: "Completed successfully",
                    has_error: false,
                },
                last_sms_sent: new Date(Date.now() - 86400000).toISOString().split('T')[0],
                calendar_horizon: 83,
                health_data_age: 3,
            })
            setLoading(false)
            return
        }

        fetchSystemStatus()
            .then(setStatus)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [isDemoMode])

    if (loading) return (
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Loading system status...
        </p>
    )

    const horizon = status?.calendar_horizon
    const healthAge = status?.health_data_age
    const lastRun = status?.last_reminder_run
    const lastSMS = status?.last_sms_sent

    const horizonColor = horizon > 30 ? 'var(--emerald-light)'
        : horizon > 14 ? '#fcd34d' : '#f87171'
    const healthColor = healthAge < 7 ? 'var(--emerald-light)'
        : healthAge < 14 ? '#fcd34d' : '#f87171'
    const runColor = lastRun?.has_error ? '#f87171' : 'var(--emerald-light)'

    const formatDate = (dateStr) => {
        if (!dateStr) return 'Unknown'
        return new Date(dateStr).toLocaleDateString('en-CA', {
            month: 'long', day: 'numeric', year: 'numeric'
        })
    }

    const formatTimestamp = (isoStr) => {
        if (!isoStr) return 'Unknown'
        return new Date(isoStr).toLocaleString('en-CA', {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        })
    }

    const rows = [
        {
            label: 'Last reminder check',
            value: lastRun?.timestamp ? formatTimestamp(lastRun.timestamp) : 'Unknown',
            status: lastRun?.status || 'Unknown',
            color: runColor,
        },
        {
            label: 'Last SMS sent',
            value: formatDate(lastSMS),
            color: 'var(--text-primary)',
        },
        {
            label: 'Calendar horizon',
            value: horizon != null ? `${horizon} days ahead` : 'Unknown',
            color: horizonColor,
        },
        {
            label: 'Health data age',
            value: healthAge != null ? `${healthAge} days old` : 'Unknown',
            color: healthColor,
        },
        {
            label: 'Last error',
            value: lastRun?.has_error ? 'Error detected — check CloudWatch' : 'None',
            color: lastRun?.has_error ? '#f87171' : 'var(--emerald-light)',
        },
    ]

    return (
        <div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>
                System Status
            </h3>

            <div style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                overflow: 'hidden',
            }}>
                {rows.map(({ label, value, color }, i) => (
                    <div key={label} style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.75rem 1rem',
                        borderBottom: i < rows.length - 1
                            ? '1px solid var(--border)' : 'none',
                    }}>
                        <span style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.8rem',
                        }}>
                            {label}
                        </span>
                        <span style={{
                            color,
                            fontSize: '0.8rem',
                            fontWeight: 500,
                            textAlign: 'right',
                        }}>
                            {value}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    )
}

// Main Settings component
export default function Settings({ healthData, fastingData, isDemoMode, token, overrides, onOverridesChange, onSignOut }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <DataStatus healthData={healthData} />
            <div style={{ height: '1px', background: 'var(--border)' }} />
            <FastingOverrides
                isDemoMode={isDemoMode}
                token={token}
                overrides={overrides}
                onOverridesChange={onOverridesChange}
                fastingData={fastingData}
            />
            <div style={{ height: '1px', background: 'var(--border)' }} />
            <SystemStatus isDemoMode={isDemoMode} />
            <div style={{ height: '1px', background: 'var(--border)' }} />
            <NotificationRecipients
                onSignOut={onSignOut}
                isDemoMode={isDemoMode}
            />
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