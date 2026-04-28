import { useEffect, useState } from 'react'
import {
    Bar,
    CartesianGrid,
    Cell,
    ComposedChart, Line,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'

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
export default function HealthTrends({ healthData: rawHealthData, fastingData, loading }) {
    const [chartData, setChartData] = useState([])
    const [activeMetric, setActiveMetric] = useState('resting_heart_rate')
    const [dateRange, setDateRange] = useState(90)   // days to show
    const [aggregated, setAggregated] = useState(true)

    // Pivot health data and merge with fasting
    useEffect(() => {
        if (!rawHealthData.length) return

        const byDate = {}
        rawHealthData.forEach(({ date, metric, value }) => {
            if (!byDate[date]) byDate[date] = { date }
            byDate[date][metric] = value
        })

        const cutoff = new Date()
        cutoff.setDate(cutoff.getDate() - dateRange)

        const processed = Object.values(byDate)
            .filter(row => new Date(row.date) >= cutoff)  // ← this line was missing
            .sort((a, b) => a.date.localeCompare(b.date))
            .map(row => ({
                ...row,
                is_fasting: !!fastingData[row.date]?.is_fasting,
                fast_type: fastingData[row.date]?.fast_type || null,
                displayDate: new Date(row.date).toLocaleDateString('en-CA', {
                    month: 'short',
                    day: 'numeric',
                }),
            }))

        const finalData = (dateRange >= 180 && aggregated)
            ? aggregateByWeek(processed)
            : processed
        setChartData(finalData)
    }, [rawHealthData, fastingData, aggregated, dateRange])

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
                                    const fastType = payload.fast_type
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
                                const fastType = payload.fast_type
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
                            {chartData.map((entry, index) => {
                                const barColors = {
                                    ramadan: '#a78bfa',
                                    weekly_sunnah: '#7dd3fc',
                                    ayyam_al_bid: '#6ee7b7',
                                    arafah: '#fdba74',
                                    ashura: '#f9a8d4',
                                    dhul_hijjah_early: '#fcd34d',
                                }
                                const fill = entry.is_fasting
                                    ? (barColors[entry.fast_type] || 'var(--gold)')
                                    : metric.color
                                return (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={fill}
                                        opacity={entry.is_fasting ? 0.85 : 0.55}
                                    />
                                )
                            })}
                        </Bar>
                    )}
                </ComposedChart>
            </ResponsiveContainer>

            {metric.type === 'bar' && (
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.6rem',
                    justifyContent: 'center',
                    marginTop: '1rem',
                }}>
                    {[
                        { color: '#a78bfa', label: 'Ramadan' },
                        { color: '#7dd3fc', label: 'Weekly Sunnah' },
                        { color: '#6ee7b7', label: 'Ayyam al-Bid' },
                        { color: '#fdba74', label: 'Arafah' },
                        { color: '#f9a8d4', label: 'Ashura' },
                        { color: '#fcd34d', label: 'Dhul Hijjah' },
                    ].map(({ color, label }) => (
                        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <div style={{ width: 10, height: 10, borderRadius: 2, background: color, opacity: 0.85 }} />
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{label}</span>
                        </div>
                    ))}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <div style={{ width: 10, height: 10, borderRadius: 2, background: metric.color, opacity: 0.55 }} />
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Non-fasting</span>
                    </div>
                </div>
            )}

            {metric.type === 'line' && (
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.6rem',
                    justifyContent: 'center',
                    marginTop: '1rem',
                }}>
                    {[
                        { type: 'ramadan', color: '#a78bfa', label: 'Ramadan' },
                        { type: 'weekly_sunnah', color: '#7dd3fc', label: 'Weekly Sunnah' },
                        { type: 'ayyam_al_bid', color: '#6ee7b7', label: 'Ayyam al-Bid' },
                        { type: 'arafah', color: '#fdba74', label: 'Arafah' },
                        { type: 'ashura', color: '#f9a8d4', label: 'Ashura' },
                        { type: 'dhul_hijjah_early', color: '#fcd34d', label: 'Dhul Hijjah' },
                    ].map(({ color, label }) => (
                        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <svg width="16" height="16" style={{ flexShrink: 0 }}>
                                <circle cx="8" cy="8" r="5.5" fill="var(--gold)" />
                                <circle cx="8" cy="8" r="3.5" fill={color} />
                            </svg>
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{label}</span>
                        </div>
                    ))}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <svg width="16" height="16">
                            <circle cx="8" cy="8" r="4.5" fill={metric.color} opacity="0.6" />
                        </svg>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Non-fasting</span>
                    </div>
                </div>
            )}

            {/* Chart note */}
            {metric.type !== 'line' && (
                <p style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.7rem',
                    textAlign: 'center',
                    marginTop: '0.75rem'
                }}>
                    Gold bars indicate fasting days · Data from Apple Health
                </p>
            )}
        </div>
    )
}