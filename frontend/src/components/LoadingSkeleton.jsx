import './LoadingSkeleton.css'

function HealthTrendsSkeleton() {
  return (
    <div className="skeleton-root">
      <div className="skeleton-metrics-row">
        {[130, 72, 118, 68].map((w, i) => (
          <div key={i} className="skeleton-block skeleton-pill" style={{ width: w }} />
        ))}
      </div>
      <div className="skeleton-stat-grid">
        <div className="skeleton-block skeleton-stat-card" />
        <div className="skeleton-block skeleton-stat-card" />
      </div>
      <div className="skeleton-controls-row">
        {[0, 1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-block skeleton-control" />
        ))}
      </div>
      <div className="skeleton-block skeleton-chart" />
      <div className="skeleton-legend-row">
        {[0, 1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-block skeleton-legend-chip" />
        ))}
      </div>
    </div>
  )
}

function FastingCalendarSkeleton() {
  return (
    <div className="skeleton-root">
      <div className="skeleton-nav">
        <div className="skeleton-block skeleton-nav-btn" />
        <div className="skeleton-nav-center">
          <div className="skeleton-block skeleton-month-title" />
          <div className="skeleton-block skeleton-hijri-title" />
        </div>
        <div className="skeleton-block skeleton-nav-btn" />
      </div>
      <div className="skeleton-weekday-row">
        {Array.from({ length: 7 }, (_, i) => (
          <div key={i} className="skeleton-block skeleton-weekday-header" />
        ))}
      </div>
      <div className="skeleton-calendar-grid">
        {Array.from({ length: 42 }, (_, i) => (
          <div key={i} className="skeleton-block skeleton-day-cell" />
        ))}
      </div>
      <div className="skeleton-legend-row">
        {[0, 1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-block skeleton-legend-chip" />
        ))}
      </div>
    </div>
  )
}

export default function LoadingSkeleton({ variant }) {
  if (variant === 'fastingCalendar') return <FastingCalendarSkeleton />
  return <HealthTrendsSkeleton />
}
