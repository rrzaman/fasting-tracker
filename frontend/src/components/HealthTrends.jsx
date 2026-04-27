import { useState, useEffect } from 'react'
import Papa from 'papaparse'
import {
    ComposedChart, Line, Bar, Cell, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'

// Fasting calendar mock (same as FastingCalendar for now)
const mockFastingData = {
    "2026-04-27": { fast_type: "weekly_sunnah", is_fasting: true },
    "2026-04-30": { fast_type: "ayyam_al_bid", is_fasting: true },
    "2026-05-01": { fast_type: "ayyam_al_bid", is_fasting: true },
    "2026-05-02": { fast_type: "ayyam_al_bid", is_fasting: true },
    "2026-05-04": { fast_type: "weekly_sunnah", is_fasting: true },
    "2026-05-07": { fast_type: "weekly_sunnah", is_fasting: true },
    "2026-05-11": { fast_type: "weekly_sunnah", is_fasting: true },
    "2026-05-14": { fast_type: "weekly_sunnah", is_fasting: true },
    "2026-05-18": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-19": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-20": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-21": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-22": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-23": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-24": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-25": { fast_type: "dhul_hijjah_early", is_fasting: true },
    "2026-05-26": { fast_type: "arafah", is_fasting: true },
    "2026-06-24": { fast_type: "ashura", is_fasting: true },
    "2026-06-25": { fast_type: "ashura", is_fasting: true },

    // Ramadan 2026: February 18th to March 19th
    ...Object.fromEntries(
        Array.from({ length: 30 }, (_, i) => {
            const d = new Date(2026, 1, 18 + i) // month 1 = February
            const str = d.toISOString().split('T')[0]
            return [str, { fast_type: "ramadan", is_fasting: true }]
        })
    ),
}

// Chart configs 
const METRICS = [
    {
        key: 'resting_heart_rate',
        label: 'Resting Heart Rate',
        unit: 'bpm',
        color: '#f87171',
        type: 'line',
    },
    {
        key: 'steps',
        label: 'Steps',
        unit: 'steps',
        color: '#7dd3fc',
        type: 'bar',
    },
    {
        key: 'active_calories',
        label: 'Active Calories',
        unit: 'kcal',
        color: '#6ee7b7',
        type: 'bar',
    },
    {
        key: 'sleep',
        label: 'Sleep',
        unit: 'hrs',
        color: '#a78bfa',
        type: 'bar',
    },
]

// Custom tooltip 
function CustomTooltip({ active, payload, label, unit, isFasting }) {
    if (!active || !payload?.length) return null
    return (
        <div style={{
            background: '#0e1a12',
            border: `1px solid ${isFasting ? 'var(--gold)' : 'var(--border)'}`,
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            fontSize: '0.8rem',
        }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>{label}</p>
            <p style={{ color: payload[0]?.color, fontWeight: 500 }}>
                {payload[0]?.value?.toFixed(1)} {unit}
            </p>
            {isFasting && (
                <p style={{ color: 'var(--gold)', fontSize: '0.7rem', marginTop: '0.25rem' }}>
                    ★ Fasting day
                </p>
            )}
        </div>
    )
}

function aggregateByWeek(data) {
    const weeks = {}

    data.forEach(row => {
        const d = new Date(row.date)
        // Get Monday of this week as the week key
        const day = d.getDay()
        const monday = new Date(d)
        monday.setDate(d.getDate() - (day === 0 ? 6 : day - 1))
        const weekKey = monday.toISOString().split('T')[0]

        if (!weeks[weekKey]) {
            weeks[weekKey] = {
                date: weekKey,
                displayDate: monday.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
                is_fasting: false,
                _counts: {},
                _sums: {},
            }
        }

        // Flag week as fasting if any day was a fast
        if (row.is_fasting) weeks[weekKey].is_fasting = true

            // Sum numeric metrics
            ;['steps', 'active_calories', 'sleep', 'resting_heart_rate'].forEach(m => {
                if (row[m] != null) {
                    weeks[weekKey]._sums[m] = (weeks[weekKey]._sums[m] || 0) + row[m]
                    weeks[weekKey]._counts[m] = (weeks[weekKey]._counts[m] || 0) + 1
                }
            })
    })

    // Calculate averages
    return Object.values(weeks)
        .map(week => {
            const result = { ...week }
                ;['steps', 'active_calories', 'sleep', 'resting_heart_rate'].forEach(m => {
                    if (week._counts[m]) {
                        result[m] = parseFloat((week._sums[m] / week._counts[m]).toFixed(1))
                    }
                })
            delete result._sums
            delete result._counts
            return result
        })
        .sort((a, b) => a.date.localeCompare(b.date))
}

// Main component
export default function HealthTrends() {
    const [rawData, setRawData] = useState([])
    const [chartData, setChartData] = useState([])
    const [activeMetric, setActiveMetric] = useState('resting_heart_rate')
    const [dateRange, setDateRange] = useState(90)   // days to show
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [aggregated, setAggregated] = useState(true)

    // Load and parse CSV 
    useEffect(() => {
        Papa.parse('/health_summary.csv', {
            download: true,
            header: true,
            dynamicTyping: true,
            complete: (results) => {
                setRawData(results.data.filter(r => r.date && r.metric && r.value != null))
                setLoading(false)
            },
            error: (err) => {
                setError(err.message)
                setLoading(false)
            }
        })
    }, [])

    // Pivot and merge with fasting data 
    useEffect(() => {
        if (!rawData.length) return

        // Group by date
        const byDate = {}
        rawData.forEach(({ date, metric, value }) => {
            if (!byDate[date]) byDate[date] = { date }
            byDate[date][metric] = value
        })

        // Convert to array, sort, filter to date range, add fasting flag
        const cutoff = new Date()
        cutoff.setDate(cutoff.getDate() - dateRange)

        const processed = Object.values(byDate)
            .filter(row => new Date(row.date) >= cutoff)
            .sort((a, b) => a.date.localeCompare(b.date))
            .map(row => ({
                ...row,
                is_fasting: !!mockFastingData[row.date]?.is_fasting,
                displayDate: new Date(row.date).toLocaleDateString('en-CA', {
                    month: 'short',
                    day: 'numeric',
                }),
            }))
        const finalData = (dateRange >= 180 && aggregated) ? aggregateByWeek(processed) : processed

        setChartData(finalData)
    }, [rawData, dateRange, aggregated])

    const handleDateRange = (d) => {
        setDateRange(d)
        setAggregated(d >= 180) // auto-aggregate for long ranges
    }

    // Metric config for active chart 
    const metric = METRICS.find(m => m.key === activeMetric)

    // Stats: fasting vs non-fasting average 
    const fastingRows = chartData.filter(d => d.is_fasting && d[activeMetric] != null)
    const nonFastingRows = chartData.filter(d => !d.is_fasting && d[activeMetric] != null)
    const avg = arr => arr.length
        ? (arr.reduce((s, d) => s + d[activeMetric], 0) / arr.length).toFixed(1)
        : '—'

    const fastingAvg = avg(fastingRows)
    const nonFastingAvg = avg(nonFastingRows)

    if (loading) return (
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
            Loading health data...
        </p>
    )

    if (error) return (
        <p style={{ color: '#f87171', textAlign: 'center', padding: '2rem' }}>
            Error loading data: {error}
        </p>
    )

    return (
        <div>
            {/* Metric selector tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                {METRICS.map(m => (
                    <button
                        key={m.key}
                        onClick={() => setActiveMetric(m.key)}
                        style={{
                            background: activeMetric === m.key ? `${m.color}22` : 'transparent',
                            border: `1px solid ${activeMetric === m.key ? m.color : 'var(--border)'}`,
                            borderRadius: '6px',
                            color: activeMetric === m.key ? m.color : 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontFamily: 'var(--font-body)',
                            padding: '0.4rem 1rem',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        {m.label}
                    </button>
                ))}
            </div>

            {/* Fasting vs non-fasting summary */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '1rem',
                marginBottom: '1.5rem',
            }}>
                <div style={{
                    background: 'rgba(240,192,64,0.06)',
                    border: '1px solid var(--gold-muted)',
                    borderRadius: '8px',
                    padding: '1rem',
                    textAlign: 'center',
                }}>
                    <p style={{ color: 'var(--gold)', fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                        Fasting days avg
                    </p>
                    <p style={{ color: 'var(--text-primary)', fontSize: '1.5rem', fontFamily: 'var(--font-display)', marginTop: '0.25rem' }}>
                        {fastingAvg} <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{metric.unit}</span>
                    </p>
                </div>
                <div style={{
                    background: 'rgba(61,189,128,0.06)',
                    border: '1px solid var(--emerald-muted)',
                    borderRadius: '8px',
                    padding: '1rem',
                    textAlign: 'center',
                }}>
                    <p style={{ color: 'var(--emerald-light)', fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                        Non-fasting days avg
                    </p>
                    <p style={{ color: 'var(--text-primary)', fontSize: '1.5rem', fontFamily: 'var(--font-display)', marginTop: '0.25rem' }}>
                        {nonFastingAvg} <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{metric.unit}</span>
                    </p>
                </div>
            </div>

            {/* Date range selector */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', justifyContent: 'flex-end' }}>
                {[30, 90, 180, 365].map(d => (
                    <button
                        key={d}
                        onClick={() => handleDateRange(d)}
                        style={{
                            background: dateRange === d ? 'rgba(240,192,64,0.1)' : 'transparent',
                            border: `1px solid ${dateRange === d ? 'var(--gold)' : 'var(--border)'}`,
                            borderRadius: '4px',
                            color: dateRange === d ? 'var(--gold)' : 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-body)',
                            padding: '0.25rem 0.6rem',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        {d}d
                    </button>
                ))}

                {/* Toggle only appears for 180d+ */}
                {dateRange >= 180 && (
                    <button
                        onClick={() => setAggregated(a => !a)}
                        style={{
                            background: aggregated ? 'rgba(240,192,64,0.08)' : 'transparent',
                            border: `1px solid ${aggregated ? 'var(--gold)' : 'var(--border)'}`,
                            borderRadius: '4px',
                            color: aggregated ? 'var(--gold)' : 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-body)',
                            padding: '0.25rem 0.6rem',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        {aggregated ? 'Weekly avg' : 'Daily'}
                    </button>
                )}
            </div>


            {/* Chart */}
            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis
                        dataKey="displayDate"
                        tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                        axisLine={{ stroke: 'var(--border)' }}
                        tickLine={false}
                        interval={
                            aggregated && dateRange >= 180
                                ? Math.floor(chartData.length / 15)
                                : dateRange === 30 ? 1
                                : dateRange === 90 ? 6
                                : dateRange === 180 ? 13
                                : 30
                        }
                    />
                    <YAxis
                        tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        width={35}
                    />
                    <Tooltip
                        content={({ active, payload, label }) => (
                            <CustomTooltip
                                active={active}
                                payload={payload}
                                label={label}
                                unit={metric.unit}
                                isFasting={payload?.[0]?.payload?.is_fasting}
                            />
                        )}
                    />

                    {metric.type === 'line' ? (
                        <Line
                            type="monotone"
                            dataKey={activeMetric}
                            stroke={metric.color}
                            isAnimationActive={true}
                            animationDuration={400}
                            strokeWidth={1.5}
                            dot={(props) => {
                                const { cx, cy, payload } = props
                                if (!payload[activeMetric]) return <g key={`empty-${payload.date}`} />

                                if (payload.is_fasting) {
                                    const fastType = mockFastingData[payload.date]?.fast_type
                                    const innerColors = {
                                        ramadan: '#a78bfa',
                                        weekly_sunnah: '#7dd3fc',
                                        ayyam_al_bid: '#6ee7b7',
                                        arafah: '#fdba74',
                                        ashura: '#f9a8d4',
                                        dhul_hijjah_early: '#fcd34d',
                                    }
                                    const innerColor = innerColors[fastType] || metric.color
                                    return (
                                        <g key={`dot-${payload.date}`} style={{ pointerEvents: 'none' }}>
                                            <circle cx={cx} cy={cy} r={5.5} fill="var(--gold)" stroke="none" />
                                            <circle cx={cx} cy={cy} r={3.5} fill={innerColor} stroke="none" />
                                        </g>
                                    )
                                }

                                return (
                                    <g key={`dot-${payload.date}`} style={{ pointerEvents: 'none' }}>
                                        <circle cx={cx} cy={cy} r={4.5} fill={metric.color} stroke="none" />
                                    </g>
                                )
                            }}
                            activeDot={(props) => {
                                const { cx, cy, payload } = props
                                const fastType = mockFastingData[payload.date]?.fast_type
                                const innerColors = {
                                    ramadan: '#a78bfa',
                                    weekly_sunnah: '#7dd3fc',
                                    ayyam_al_bid: '#6ee7b7',
                                    arafah: '#fdba74',
                                    ashura: '#f9a8d4',
                                    dhul_hijjah_early: '#fcd34d',
                                }
                                const innerColor = payload.is_fasting
                                    ? (innerColors[fastType] || metric.color)
                                    : metric.color
                                return (
                                    <g key={`active-${payload.date}`}>
                                        <circle cx={cx} cy={cy} r={9} fill="var(--gold)" stroke="none" opacity={0.2} />
                                        <circle cx={cx} cy={cy} r={6.5} fill="var(--gold)" stroke="none" />
                                        <circle cx={cx} cy={cy} r={4.5} fill={innerColor} stroke="none" />
                                    </g>
                                )
                            }}
                            connectNulls
                        />
                    ) : (
                        <Bar
                            dataKey={activeMetric}
                            radius={[2, 2, 0, 0]}
                            isAnimationActive={true}
                            animationDuration={400}
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry.is_fasting ? 'var(--gold)' : metric.color}
                                    opacity={entry.is_fasting ? 0.9 : 0.6}
                                />
                            ))}
                        </Bar>
                    )}
                </ComposedChart>
            </ResponsiveContainer>

            {/* Chart note */}
            <p style={{
                color: 'var(--text-muted)',
                fontSize: '0.7rem',
                textAlign: 'center',
                marginTop: '0.75rem'
            }}>
                Gold markers indicate fasting days · Data from Apple Health
            </p>
        </div>
    )
}