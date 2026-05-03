import { useEffect, useMemo, useRef, useState } from 'react'
import LoadingSkeleton from './LoadingSkeleton'
import {
    Bar,
    CartesianGrid,
    Cell,
    ComposedChart, Line,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts'
import { FAST_COLORS, FAST_LABELS } from '../constants'

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

function computeInsights(fastingRows, nonFastingRows, processedData, metricKey) {
    if (fastingRows.length < 3 || nonFastingRows.length < 3) return null

    const fastingVals = fastingRows.map(d => d[metricKey])
    const nonFastingVals = nonFastingRows.map(d => d[metricKey])

    const mean = arr => arr.reduce((s, v) => s + v, 0) / arr.length
    const variance = arr => {
        const m = mean(arr)
        return arr.reduce((s, v) => s + (v - m) ** 2, 0) / (arr.length - 1)
    }

    const fastMean = mean(fastingVals)
    const nonFastMean = mean(nonFastingVals)
    const diff = fastMean - nonFastMean
    const pctDiff = ((diff / nonFastMean) * 100).toFixed(1)

    // Welch's t-test approximation
    const se = Math.sqrt(variance(fastingVals) / fastingVals.length +
        variance(nonFastingVals) / nonFastingVals.length)
    const tStat = Math.abs(diff / se)
    const significant = tStat > 1.96  // ~95% confidence

    // Linear regression slope over time
    const allRows = [...processedData].filter(d => d[metricKey] != null)
    const n = allRows.length
    if (n < 5) return { diff, pctDiff, significant, slope: null }

    const xs = allRows.map((_, i) => i)
    const ys = allRows.map(d => d[metricKey])
    const xMean = mean(xs)
    const yMean = mean(ys)
    const slope = xs.reduce((s, x, i) => s + (x - xMean) * (ys[i] - yMean), 0) /
        xs.reduce((s, x) => s + (x - xMean) ** 2, 0)

    // Consistency — % of fasting days below non-fasting avg (for HR, lower is better)
    const isLowerBetter = metricKey === 'resting_heart_rate'
    const improvedCount = fastingVals.filter(v =>
        isLowerBetter ? v < nonFastMean : v > nonFastMean
    ).length
    const consistency = Math.round((improvedCount / fastingVals.length) * 100)

    function partialCorrelation(x, y, z) {
        // Correlation between x and y controlling for z
        // Uses the formula: r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1-r_xz²)(1-r_yz²))
        const n = x.length
        if (n < 5) return null

        const mean = arr => arr.reduce((s, v) => s + v, 0) / arr.length
        const pearson = (a, b) => {
            const ma = mean(a), mb = mean(b)
            const num = a.reduce((s, v, i) => s + (v - ma) * (b[i] - mb), 0)
            const den = Math.sqrt(
                a.reduce((s, v) => s + (v - ma) ** 2, 0) *
                b.reduce((s, v) => s + (v - mb) ** 2, 0)
            )
            return den === 0 ? 0 : num / den
        }

        const rxy = pearson(x, y)
        const rxz = pearson(x, z)
        const ryz = pearson(y, z)

        const num = rxy - rxz * ryz
        const den = Math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
        return den === 0 ? null : num / den
    }

    // Only for resting_heart_rate
    let partialCorr = null
    if (metricKey === 'resting_heart_rate') {
        // Combine fasting and non-fasting for full dataset
        const allHR = processedData
            .filter(d => d['resting_heart_rate'] != null && d['sleep'] != null)
            .map(d => d['resting_heart_rate'])
        const allSlp = processedData
            .filter(d => d['resting_heart_rate'] != null && d['sleep'] != null)
            .map(d => d['sleep'])
        const allFasting = processedData
            .filter(d => d['resting_heart_rate'] != null && d['sleep'] != null)
            .map(d => d.is_fasting ? 1 : 0)

        partialCorr = partialCorrelation(allFasting, allHR, allSlp)
    }

    return { diff, pctDiff, significant, slope, consistency, partialCorr }
}

// Custom tooltip 
function CustomTooltip({ active, payload, label, unit, isFasting, isAggregated, fastingDaysCount, tooltipDate, fastType, fastTypes }) {
    if (!active || !payload?.length) return null
    return (
        <div style={{
            background: '#0e1a12',
            border: `1px solid ${isFasting ? 'var(--gold)' : 'var(--border)'}`,
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            fontSize: '0.8rem',
            zIndex: 100,
        }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>{isAggregated ? tooltipDate : label}</p>
            <p style={{ color: payload[0]?.color, fontWeight: 500 }}>
                {payload[0]?.value?.toFixed(1)} {unit}
            </p>
            {isAggregated && isFasting && (
                <div style={{ marginTop: '0.5rem' }}>
                    <p style={{ color: 'var(--gold)', fontSize: '0.7rem', fontWeight: 500 }}>
                        ★ {fastingDaysCount} fasting days this week
                    </p>
                    {fastTypes && Object.entries(fastTypes).map(([type, count]) => (
                        <p key={type} style={{ color: 'var(--text-muted)', fontSize: '0.65rem', marginLeft: '0.8rem', marginTop: '0.2rem' }}>
                            • {count}x {FAST_LABELS[type] || 'Fast'}
                        </p>
                    ))}
                </div>
            )}
            {!isAggregated && isFasting && (
                <p style={{ color: 'var(--gold)', fontSize: '0.7rem', marginTop: '0.25rem', fontWeight: 500 }}>
                    ★ {fastType ? FAST_LABELS[fastType] || 'Fasting day' : 'Fasting day'}
                </p>
            )}
        </div>
    )
}

function aggregateByWeek(data) {
    const weeks = {}

    data.forEach(row => {
        const [y, m, dayOfMonth] = row.date.split('-')
        const d = new Date(parseInt(y), parseInt(m) - 1, parseInt(dayOfMonth))
        const day = d.getDay()
        const monday = new Date(d)
        monday.setDate(d.getDate() - (day === 0 ? 6 : day - 1))

        const yyyy = monday.getFullYear()
        const mm = String(monday.getMonth() + 1).padStart(2, '0')
        const dd = String(monday.getDate()).padStart(2, '0')
        const weekKey = `${yyyy}-${mm}-${dd}`

        if (!weeks[weekKey]) {
            const endOfWeek = new Date(monday)
            endOfWeek.setDate(monday.getDate() + 6)
            const startStr = monday.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })
            const endStr = endOfWeek.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })

            weeks[weekKey] = {
                date: weekKey,
                displayDate: startStr,
                tooltipDate: `${startStr} - ${endStr}`,
                is_fasting: false,
                is_aggregated: true,
                fasting_days_count: 0,
                fast_types: {},
                _counts: {},
                _sums: {},
            }
        }

        if (row.is_fasting) {
            weeks[weekKey].is_fasting = true
            weeks[weekKey].fasting_days_count += 1
            if (row.fast_type) {
                weeks[weekKey].fast_types[row.fast_type] = (weeks[weekKey].fast_types[row.fast_type] || 0) + 1
            }
        }

        // Sum numeric metrics
        ;['steps', 'active_calories', 'sleep', 'resting_heart_rate'].forEach(m => {
            if (row[m] != null) {
                weeks[weekKey]._sums[m] = (weeks[weekKey]._sums[m] || 0) + row[m]
                weeks[weekKey]._counts[m] = (weeks[weekKey]._counts[m] || 0) + 1
            }
        })
    })

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

function InsightsPanel({ insights, metric, fastingCount, nonFastingCount }) {
    const [expanded, setExpanded] = useState(true)
    if (!insights) return null

    const { diff, pctDiff, significant, slope, consistency } = insights
    const isLowerBetter = metric.key === 'resting_heart_rate'
    const direction = diff < 0 ? 'lower' : 'higher'
    const isGood = isLowerBetter ? diff < 0 : diff > 0
    const goodColor = 'var(--emerald-light)'
    const badColor = '#f87171'
    const neutralColor = 'var(--text-secondary)'

    const diffColor = Math.abs(diff) < 0.5 ? neutralColor : isGood ? goodColor : badColor

    const slopeLabel = !slope ? null
        : Math.abs(slope) < 0.01 ? 'Stable over this period'
            : slope < 0 ? `Trending down ${Math.abs(slope * 7).toFixed(2)} ${metric.unit}/week`
                : `Trending up ${(slope * 7).toFixed(2)} ${metric.unit}/week`

    const slopeColor = !slope ? neutralColor
        : (isLowerBetter ? slope < 0 : slope > 0) ? goodColor : badColor

    return (
        <div style={{
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            marginBottom: '1.25rem',
            overflow: 'hidden',
        }}>
            <button
                onClick={() => setExpanded(e => !e)}
                style={{
                    alignItems: 'center',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-body)',
                    gap: '0.5rem',
                    justifyContent: 'space-between',
                    letterSpacing: '0.08em',
                    padding: '0.6rem 1rem',
                    textTransform: 'uppercase',
                    width: '100%',
                }}
            >
                <span>✦ Insights ({fastingCount} fasting days vs {nonFastingCount} non-fasting)</span>
                <span style={{ opacity: 0.5 }}>{expanded ? '▲' : '▼'}</span>
            </button>

            {expanded && (
                <div style={{
                    borderTop: '1px solid var(--border)',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                }}>
                    {/* Fasting difference */}
                    <div style={chipStyle}>
                        <span style={{ color: diffColor, fontWeight: 500 }}>
                            {Math.abs(diff).toFixed(1)} {metric.unit} {direction}
                        </span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                            {' '}on fasting days ({pctDiff > 0 ? '+' : ''}{pctDiff}%)
                        </span>
                        {significant ? (
                            <span style={{
                                background: 'rgba(61,189,128,0.1)',
                                border: '1px solid var(--emerald-muted)',
                                borderRadius: '4px',
                                color: goodColor,
                                fontSize: '0.6rem',
                                marginLeft: '0.4rem',
                                padding: '1px 5px',
                            }}>significant</span>
                        ) : (
                            <span style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                color: 'var(--text-muted)',
                                fontSize: '0.6rem',
                                marginLeft: '0.4rem',
                                padding: '1px 5px',
                            }}>not significant</span>
                        )}
                    </div>

                    {/* Consistency */}
                    {consistency != null && (
                        <div style={chipStyle}>
                            <span style={{ color: consistency >= 60 ? goodColor : neutralColor, fontWeight: 500 }}>
                                {consistency}%
                            </span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                                {' '}of fasting days {isLowerBetter ? 'below' : 'above'} non-fasting avg
                            </span>
                        </div>
                    )}

                    {/* Trend */}
                    {slopeLabel && (
                        <div style={chipStyle}>
                            <span style={{ color: slopeColor, fontWeight: 500 }}>
                                {slopeLabel}
                            </span>
                        </div>
                    )}

                    {/* Partial Correlation, heart rate controllin for sleep */}
                    {insights.partialCorr != null && metric.key === 'resting_heart_rate' && (
                        <div style={chipStyle}>
                            <span style={{
                                color: insights.partialCorr < -0.1 ? goodColor : neutralColor,
                                fontWeight: 500
                            }}>
                                r = {insights.partialCorr.toFixed(2)}
                            </span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                                {' '}partial r (sleep-adjusted)
                            </span>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

const chipStyle = {
    alignItems: 'center',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid var(--border)',
    borderRadius: '6px',
    display: 'flex',
    flexWrap: 'wrap',
    fontSize: '0.78rem',
    gap: '0.2rem',
    padding: '0.4rem 0.75rem',
}

// Animates between numeric values. On first mount counts from 0;
// on subsequent changes animates from the current displayed position.
function CountUp({ value }) {
    const [display, setDisplay] = useState('0')
    const raf = useRef(null)
    const fromRef = useRef(0)  // tracks live animated position

    useEffect(() => {
        cancelAnimationFrame(raf.current)
        const target = parseFloat(value)
        if (isNaN(target)) { setDisplay(value); return }

        const from = fromRef.current
        const decimals = String(value).includes('.') ? String(value).split('.')[1].length : 0
        const start = performance.now()

        const tick = (now) => {
            const t = Math.min((now - start) / 600, 1)
            const eased = -(Math.cos(Math.PI * t) - 1) / 2  // sine ease-in-out
            const current = from + (target - from) * eased
            fromRef.current = current
            setDisplay(current.toFixed(decimals))
            if (t < 1) raf.current = requestAnimationFrame(tick)
            else {
                fromRef.current = target
                setDisplay(String(value))
            }
        }
        raf.current = requestAnimationFrame(tick)
        return () => cancelAnimationFrame(raf.current)
    }, [value])

    return display
}

// Main component
export default function HealthTrends({ healthData: rawHealthData, fastingData, loading, focusDate, clearFocus }) {
    const [activeMetric, setActiveMetric] = useState('resting_heart_rate')
    const [dateRange, setDateRange] = useState(90)
    const [aggregated, setAggregated] = useState(true)

    const processedData = useMemo(() => {
        if (!rawHealthData.length) return []

        const byDate = {}
        rawHealthData.forEach(({ date, metric, value }) => {
            if (!byDate[date]) byDate[date] = { date }
            byDate[date][metric] = value
        })

        let startDate, endDate;
        if (focusDate) {
            const [y, m, d] = focusDate.split('-');
            const fd = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
            startDate = new Date(fd);
            startDate.setDate(startDate.getDate() - 15);
            endDate = new Date(fd);
            endDate.setDate(endDate.getDate() + 15);
        } else {
            endDate = new Date();
            startDate = new Date();
            startDate.setDate(startDate.getDate() - dateRange);
        }

        return Object.values(byDate)
            .filter(row => {
                const [y, m, d] = row.date.split('-')
                const rowDate = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
                return rowDate >= startDate && rowDate <= endDate
            })
            .sort((a, b) => a.date.localeCompare(b.date))
            .map(row => {
                const [y, m, dayOfMonth] = row.date.split('-')
                const localD = new Date(parseInt(y), parseInt(m) - 1, parseInt(dayOfMonth))
                return {
                    ...row,
                    is_fasting: !!fastingData[row.date]?.is_fasting,
                    fast_type: fastingData[row.date]?.fast_type || null,
                    displayDate: localD.toLocaleDateString('en-CA', {
                        month: 'short',
                        day: 'numeric',
                    }),
                }
            })
    }, [rawHealthData, fastingData, dateRange, focusDate])

    const chartData = useMemo(() => {
        return (!focusDate && dateRange >= 180 && aggregated)
            ? aggregateByWeek(processedData)
            : processedData
    }, [processedData, aggregated, dateRange, focusDate])

    const handleDateRange = (d) => {
        setDateRange(d)
        setAggregated(d >= 180)
    }

    const metric = METRICS.find(m => m.key === activeMetric)

    const fastingRows = processedData.filter(d => d.is_fasting && d[activeMetric] != null)
    const nonFastingRows = processedData.filter(d => !d.is_fasting && d[activeMetric] != null)
    const avg = arr => arr.length
        ? (arr.reduce((s, d) => s + d[activeMetric], 0) / arr.length).toFixed(1)
        : '—'

    const insights = useMemo(() =>
        computeInsights(fastingRows, nonFastingRows, processedData, activeMetric),
        [fastingRows, nonFastingRows, processedData, activeMetric]
    )

    const fastingAvg = avg(fastingRows)
    const nonFastingAvg = avg(nonFastingRows)

    if (loading) return <LoadingSkeleton variant="healthTrends" />

    return (
        <div>
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
                        <CountUp value={fastingAvg} /> <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{metric.unit}</span>
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
                        <CountUp value={nonFastingAvg} /> <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{metric.unit}</span>
                    </p>
                </div>
            </div>

            <InsightsPanel
                insights={insights}
                metric={metric}
                fastingCount={fastingRows.length}
                nonFastingCount={nonFastingRows.length}
            />

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', justifyContent: 'flex-end', alignItems: 'center' }}>
                {focusDate && (
                    <div style={{ marginRight: 'auto', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ color: 'var(--gold)', fontSize: '0.85rem', fontWeight: 500 }}>
                            Focused: {new Date(focusDate.split('-')[0], focusDate.split('-')[1] - 1, focusDate.split('-')[2]).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            {(() => {
                                const focusedRow = processedData.find(d => d.date === focusDate);
                                return focusedRow?.is_fasting ? (
                                    <span style={{ color: FAST_COLORS[focusedRow.fast_type] || 'var(--gold)' }}>
                                        {` (${FAST_LABELS[focusedRow.fast_type] || 'Fasting'})`}
                                    </span>
                                ) : null;
                            })()}
                        </span>
                        <button
                            onClick={clearFocus}
                            style={{
                                background: 'transparent',
                                border: '1px solid var(--emerald-muted)',
                                borderRadius: '4px',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                padding: '0.25rem 0.6rem',
                                transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = 'rgba(82, 212, 148, 0.1)';
                                e.target.style.color = 'var(--text-primary)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = 'transparent';
                                e.target.style.color = 'var(--text-secondary)';
                            }}
                        >
                            Clear Focus
                        </button>
                    </div>
                )}

                {!focusDate && [30, 90, 180, 365].map(d => (
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

                {!focusDate && dateRange >= 180 && (
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

            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <defs>
                        {aggregated && dateRange >= 180 && chartData.map((week, index) => {
                            if (!week.is_aggregated || !week.is_fasting) return null;
                            const gradientId = `grad-${index}`;
                            const totalDays = 7;
                            const nonFastingCount = totalDays - week.fasting_days_count;
                            const stops = [];
                            let currentPct = 0;
                            Object.entries(week.fast_types).forEach(([type, count]) => {
                                if (count > 0 && FAST_COLORS[type]) {
                                    const pctStrStart = `${currentPct}%`;
                                    currentPct += (count / totalDays) * 100;
                                    const pctStrEnd = `${currentPct}%`;
                                    stops.push(<stop key={`${type}-start`} offset={pctStrStart} stopColor={FAST_COLORS[type]} />);
                                    stops.push(<stop key={`${type}-end`} offset={pctStrEnd} stopColor={FAST_COLORS[type]} />);
                                }
                            });
                            if (nonFastingCount > 0) {
                                const pctStrStart = `${currentPct}%`;
                                stops.push(<stop key="non-fasting-start" offset={pctStrStart} stopColor={metric.type === 'bar' ? 'rgba(255, 255, 255, 0.12)' : metric.color} />);
                                stops.push(<stop key="non-fasting-end" offset="100%" stopColor={metric.type === 'bar' ? 'rgba(255, 255, 255, 0.12)' : metric.color} />);
                            }
                            return (
                                <linearGradient key={gradientId} id={gradientId} x1="0" y1="1" x2="0" y2="0">
                                    {stops}
                                </linearGradient>
                            );
                        })}
                    </defs>
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

                    {focusDate && (
                        <ReferenceLine
                            x={new Date(focusDate.split('-')[0], focusDate.split('-')[1] - 1, focusDate.split('-')[2]).toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })}
                            stroke="var(--gold)"
                            strokeDasharray="3 3"
                            opacity={0.6}
                        />
                    )}

                    <Tooltip
                        content={({ active, payload, label }) => {
                            const data = payload?.[0]?.payload;
                            return (
                                <CustomTooltip
                                    active={active}
                                    payload={payload}
                                    label={label}
                                    unit={metric.unit}
                                    isFasting={data?.is_fasting}
                                    isAggregated={data?.is_aggregated}
                                    fastingDaysCount={data?.fasting_days_count}
                                    tooltipDate={data?.tooltipDate}
                                    fastType={data?.fast_type}
                                    fastTypes={data?.fast_types}
                                />
                            )
                        }}
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
                                const { cx, cy, payload, index } = props
                                if (!payload[activeMetric]) return <g key={`empty-${payload.date}`} />
                                if (payload.is_aggregated) {
                                    if (payload.is_fasting) {
                                        return (
                                            <g key={`dot-${payload.date}`} style={{ pointerEvents: 'none' }}>
                                                <circle cx={cx} cy={cy} r={6.5} fill={`url(#grad-${index})`} stroke="var(--gold)" strokeWidth={1} />
                                            </g>
                                        )
                                    }
                                } else if (payload.is_fasting) {
                                    const innerColor = FAST_COLORS[payload.fast_type] || metric.color
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
                                const { cx, cy, payload, index } = props
                                if (payload.is_aggregated && payload.is_fasting) {
                                    return (
                                        <g key={`active-${payload.date}`}>
                                            <circle cx={cx} cy={cy} r={11} fill="var(--gold)" stroke="none" opacity={0.2} />
                                            <circle cx={cx} cy={cy} r={7.5} fill={`url(#grad-${index})`} stroke="var(--gold)" strokeWidth={1.5} />
                                        </g>
                                    )
                                }
                                const innerColor = payload.is_fasting && !payload.is_aggregated
                                    ? (FAST_COLORS[payload.fast_type] || metric.color)
                                    : metric.color
                                return (
                                    <g key={`active-${payload.date}`}>
                                        <circle cx={cx} cy={cy} r={9} fill={payload.is_fasting ? "var(--gold)" : metric.color} stroke="none" opacity={0.2} />
                                        <circle cx={cx} cy={cy} r={6.5} fill={payload.is_fasting ? "var(--gold)" : metric.color} stroke="none" />
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
                                let fill = 'rgba(255, 255, 255, 0.12)';
                                let stroke = "none";
                                if (entry.is_aggregated && entry.is_fasting) {
                                    fill = `url(#grad-${index})`;
                                    stroke = "var(--border)";
                                } else if (entry.is_fasting) {
                                    fill = FAST_COLORS[entry.fast_type] || 'var(--gold)';
                                    if (dateRange < 180) {
                                        stroke = "var(--gold)";
                                    }
                                }
                                return (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={fill}
                                        stroke={stroke}
                                        strokeWidth={1}
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
                        { color: FAST_COLORS.ramadan, label: 'Ramadan' },
                        { color: FAST_COLORS.weekly_sunnah, label: 'Weekly Sunnah' },
                        { color: FAST_COLORS.ayyam_al_bid, label: 'Ayyam al-Bid' },
                        { color: FAST_COLORS.arafah, label: 'Arafah' },
                        { color: FAST_COLORS.ashura, label: 'Ashura' },
                        { color: FAST_COLORS.dhul_hijjah_early, label: 'Dhul Hijjah' },
                    ].map(({ color, label }) => (
                        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <div style={{ width: 10, height: 10, borderRadius: 2, background: color, opacity: 0.85 }} />
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{label}</span>
                        </div>
                    ))}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <div style={{ width: 10, height: 10, borderRadius: 2, background: 'rgba(255, 255, 255, 0.12)' }} />
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
                        { type: 'ramadan', color: FAST_COLORS.ramadan, label: 'Ramadan' },
                        { type: 'weekly_sunnah', color: FAST_COLORS.weekly_sunnah, label: 'Weekly Sunnah' },
                        { type: 'ayyam_al_bid', color: FAST_COLORS.ayyam_al_bid, label: 'Ayyam al-Bid' },
                        { type: 'arafah', color: FAST_COLORS.arafah, label: 'Arafah' },
                        { type: 'ashura', color: FAST_COLORS.ashura, label: 'Ashura' },
                        { type: 'dhul_hijjah_early', color: FAST_COLORS.dhul_hijjah_early, label: 'Dhul Hijjah' },
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
                            <circle cx="8" cy="8" r="5.5" fill={metric.color} />
                        </svg>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Non-fasting</span>
                    </div>
                </div>
            )}

            {/* Chart note */}
            {metric.type !== 'line' ? (
                <p style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.7rem',
                    textAlign: 'center',
                    marginTop: '0.75rem'
                }}>
                    Gold borders indicate fasting days · Data from Apple Health
                </p>
            ) : (
                <p style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.7rem',
                    textAlign: 'center',
                    marginTop: '0.75rem'
                }}>
                    Gold dots indicate fasting days · Data from Apple Health
                </p>
            )}
        </div>
    )
}