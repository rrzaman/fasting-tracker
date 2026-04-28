import { useEffect, useState } from 'react'
import { useSwipeable } from 'react-swipeable'

const HIJRI_MONTHS = {
  1: "Muharram",
  2: "Safar",
  3: "Rabi al-Awwal",
  4: "Rabi al-Thani",
  5: "Jumada al-Awwal",
  6: "Jumada al-Thani",
  7: "Rajab",
  8: "Shaban",
  9: "Ramadan",
  10: "Shawwal",
  11: "Dhul Qadah",
  12: "Dhul Hijjah",
}

const fastTypeToClass = {
  weekly_sunnah: 'sunnah',
  ramadan: 'ramadan',
  ayyam_al_bid: 'ayyam',
  arafah: 'arafah',
  ashura: 'ashura',
  dhul_hijjah_early: 'special',
  prohibited: 'prohibited',
  extra: 'extra',
  skipped: 'skipped',
}

const fastTypeToLabel = {
  weekly_sunnah: 'Weekly Sunnah',
  ramadan: 'Ramadan',
  ayyam_al_bid: 'Ayyam al-Bid',
  arafah: 'Arafah',
  ashura: 'Ashura',
  dhul_hijjah_early: 'Dhul Hijjah',
  prohibited: 'Prohibited',
  extra: 'Extra fast',
  skipped: 'Skipped',
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const hijriCache = {};

async function fetchHijriMonth(year, month) {
  const cacheKey = `${year}-${month}`;
  if (hijriCache[cacheKey]) return hijriCache[cacheKey];

  try {
    const res = await fetch(`https://api.aladhan.com/v1/gToHCalendar/${month}/${year}`)
    const data = await res.json()
    const hijriMap = {}
    const monthNames = new Set()
    const years = new Set()

    if (data.data && Array.isArray(data.data)) {
      data.data.forEach(item => {
        const gDate = item.gregorian.date.split('-')
        const dateStr = `${gDate[2]}-${gDate[1]}-${gDate[0]}`
        hijriMap[dateStr] = item.hijri.day

        // Use our Python dictionary mapping
        const properMonthName = HIJRI_MONTHS[item.hijri.month.number]
        if (properMonthName) monthNames.add(properMonthName)
        years.add(item.hijri.year)
      })
    }

    const result = {
      dates: hijriMap,
      months: Array.from(monthNames),
      years: Array.from(years)
    };

    hijriCache[cacheKey] = result;
    return result;
  } catch {
    return { dates: {}, months: [], years: [] }
  }
}

export default function FastingCalendar({ fastingData, loading }) {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth())
  const [hoveredDay, setHoveredDay] = useState(null)
  const [highlightedType, setHighlightedType] = useState(null)
  const [hijriDates, setHijriDates] = useState({})
  const [hijriHeader, setHijriHeader] = useState('')
  const [isLoadingHijri, setIsLoadingHijri] = useState(false)

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const prevMonthDays = new Date(year, month, 0).getDate()

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1) }
    else setMonth(m => m - 1)
  }

  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1) }
    else setMonth(m => m + 1)
  }

  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => nextMonth(),
    onSwipedRight: () => prevMonth(),
    preventScrollOnSwipe: true,
    trackMouse: false
  })

  useEffect(() => {
    const fetchAll = async () => {
        setIsLoadingHijri(true)

        const prevM = month === 0 ? 12 : month
        const prevY = month === 0 ? year - 1 : year
        const currM = month + 1
        const currY = year
        const nextM = month === 11 ? 1 : month + 2
        const nextY = month === 11 ? year + 1 : year

        const [prevData, currData, nextData] = await Promise.all([
            fetchHijriMonth(prevY, prevM),
            fetchHijriMonth(currY, currM),
            fetchHijriMonth(nextY, nextM)
        ])

        setHijriDates({ ...prevData.dates, ...currData.dates, ...nextData.dates })

        if (currData.months.length > 0) {
            setHijriHeader(`${currData.months.join(' - ')} ${currData.years.join(' - ')}`)
        } else {
            setHijriHeader('')
        }

        setIsLoadingHijri(false)
    }
    fetchAll()
}, [year, month])

  const currentMonthCounts = {}

  if (loading) return <p style={{ color: 'var(--text-secondary)' }}>Loading calendar...</p>


  Object.keys(fastTypeToLabel).forEach(type => {
    currentMonthCounts[type] = 0
  })

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const record = fastingData[dateStr]
    if (record && record.is_fasting) {
      currentMonthCounts[record.fast_type] += 1
    }
  }

  const cells = []

  for (let i = firstDay - 1; i >= 0; i--) {
    cells.push({ day: prevMonthDays - i, currentMonth: false, offset: -1 })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, currentMonth: true, offset: 0 })
  }
  let nextDay = 1
  while (cells.length < 42) {
    cells.push({ day: nextDay++, currentMonth: false, offset: 1 })
  }

  return (
    <div {...swipeHandlers}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.5rem'
      }}>
        <button onClick={prevMonth} style={navBtnStyle}>‹</button>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: 'var(--text-primary)', margin: 0, lineHeight: 1.2 }}>
            {MONTHS[month]} {year}
          </h2>
          <div style={{
            fontSize: '0.85rem',
            color: 'var(--text-hijri)',
            marginTop: '4px',
            fontFamily: 'var(--font-body)',
            letterSpacing: '0.05em'
          }}>
            {isLoadingHijri ? '...' : hijriHeader}
          </div>
        </div>
        <button onClick={nextMonth} style={navBtnStyle}>›</button>
      </div>

      <div style={gridStyle}>
        {WEEKDAYS.map(day => (
          <div key={day} style={headerCellStyle}>{day}</div>
        ))}

        {cells.map((cell, idx) => {
          const m = month + cell.offset
          const y = m < 0 ? year - 1 : m > 11 ? year + 1 : year
          const mm = ((m % 12) + 12) % 12
          const dateStr = `${y}-${String(mm + 1).padStart(2, '0')}-${String(cell.day).padStart(2, '0')}`
          const record = fastingData[dateStr]
          const isToday = cell.day === today.getDate() &&
            mm === today.getMonth() &&
            y === today.getFullYear()
          const isHovered = hoveredDay === dateStr
          const fastClass = record?.is_fasting ? fastTypeToClass[record.fast_type] : null
          const hijriDay = hijriDates[dateStr]

          // Visual distinction logic
          const isHighlighted = highlightedType !== null;
          const matchesHighlight = record?.fast_type === highlightedType;

          // If a highlight is active and this cell doesn't match, heavily dim it
          const fadeOut = isHighlighted && !matchesHighlight;

          const cellBackground = isHovered && cell.currentMonth && !fadeOut ? 'rgba(240,192,64,0.08)' :
            isToday && !fadeOut ? 'rgba(240,192,64,0.1)' :
              cell.currentMonth ? 'rgba(255, 255, 255, 0.03)' :
                'transparent';

          // Drop opacity to 0.1 if faded out
          const textOpacity = cell.currentMonth ? (fadeOut ? 0.1 : 1) : 0.25;

          return (
            <div
              key={`${dateStr}-${idx}`}
              onMouseEnter={() => setHoveredDay(dateStr)}
              onMouseLeave={() => setHoveredDay(null)}
              style={{
                ...dayCellStyle,
                background: cellBackground,
                border: isToday
                  ? '1px solid var(--gold)'
                  : isHovered && cell.currentMonth
                    ? '1px solid var(--emerald-muted)'
                    : '1px solid transparent',
              }}
            >
              {/* Gregorian day number */}
              <span style={{
                fontSize: '0.85rem',
                color: isToday ? 'var(--gold)' : 'var(--text-primary)',
                fontWeight: isToday ? '500' : '300',
                lineHeight: 1,
                opacity: textOpacity,
              }}>
                {cell.day}
              </span>

              {/* Hijri day number */}
              {isLoadingHijri ? (
                <span style={{ fontSize: '0.65rem', color: 'var(--text-hijri)', marginTop: '2px', opacity: textOpacity }}>...</span>
              ) : hijriDay ? (
                <span style={{ fontSize: '0.65rem', color: 'var(--text-hijri)', marginTop: '2px', opacity: textOpacity }}>
                  {hijriDay}
                </span>
              ) : null}

              {/* Fast type badge */}
              {fastClass && (
                <span
                  className={`badge badge--${fastClass}`}
                  style={{
                    fontSize: '0.55rem',
                    marginTop: 'auto',
                    marginBottom: '2px',
                    opacity: textOpacity, // <-- Now the badge fades out with the text!
                    filter: cell.currentMonth ? 'none' : 'grayscale(50%)'
                  }}
                >
                  {fastTypeToLabel[record.fast_type]}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.75rem', // Slightly larger gap so they don't touch when scaled
        marginTop: '1.5rem',
        paddingTop: '1rem',
        borderTop: '1px solid var(--border)',
        justifyContent: 'center',
      }}>
        {Object.entries(fastTypeToLabel).map(([type, label]) => {
          const count = currentMonthCounts[type];
          const isSelected = highlightedType === type;
          const isHighlighted = highlightedType !== null;

          return (
            <button
              key={type}
              onClick={() => {
                // Notice we removed the "if count is 0" check!
                // Now you can click ANY badge to highlight it.
                setHighlightedType(isSelected ? null : type);
              }}
              className={`badge badge--${fastTypeToClass[type]}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center', // <-- ADDED THIS: Centers text & number
                gap: '0.4rem',
                padding: '0.4rem 0.6rem',
                textTransform: 'none',
                fontSize: '0.75rem',
                border: isSelected ? '1px solid currentColor' : '1px solid transparent',
                boxShadow: isSelected ? 'inset 0 0 20px currentColor' : 'none',
                opacity: isHighlighted && !isSelected ? 0.3 : 1,
                cursor: 'pointer',
                transform: isSelected ? 'scale(1.05)' : 'scale(1)',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                flex: '0 1 auto',
              }}
            >
              <span style={{ fontWeight: 600 }}>{label}</span>

              {/* Count Badge - Now ALWAYS renders so the button size stays constant */}
              <span style={{
                background: 'rgba(255,255,255,0.15)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.65rem',
                opacity: count > 0 ? 1 : 0.3 // Dim the 0 so it's clear it's empty
              }}>
                {count}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(7, 1fr)',
  gap: '6px',
}

const headerCellStyle = {
  textAlign: 'center',
  fontSize: '0.7rem',
  letterSpacing: '0.1em',
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  padding: '0.5rem 0',
  fontFamily: 'var(--font-body)',
}

const dayCellStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'flex-start',
  padding: '0.5rem 0.25rem',
  borderRadius: '8px',
  height: '100px',
  overflow: 'hidden',
  cursor: 'default',
  transition: 'all 0.15s ease',
}

const navBtnStyle = {
  background: 'none',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  fontSize: '1.2rem',
  padding: '0.25rem 0.75rem',
  transition: 'all 0.2s ease',
}