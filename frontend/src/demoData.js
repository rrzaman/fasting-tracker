// Synthetic data for demo mode — not real health data
function generateDemoData() {
    const fastingMap = {}
    const healthArray = []

    const start = new Date(2025, 5, 1) // June 2025
    const end = new Date(2026, 6, 31)  // July 2026

    // Define fasting periods
    const fastingPeriods = [
        // Ramadan 2026
        { start: new Date(2026, 1, 18), end: new Date(2026, 2, 19), type: 'ramadan', hijri_month: 9 },
        // Dhul Hijjah early 2026
        { start: new Date(2026, 4, 18), end: new Date(2026, 4, 25), type: 'dhul_hijjah_early', hijri_month: 12 },
    ]

    // Ayyam al-Bid — 13th-15th of each month (approximate)
    const ayyamDates = [
        '2025-07-09', '2025-07-10', '2025-07-11',
        '2025-08-07', '2025-08-08', '2025-08-09',
        '2025-09-06', '2025-09-07', '2025-09-08',
        '2025-10-05', '2025-10-06', '2025-10-07',
        '2025-11-03', '2025-11-04', '2025-11-05',
        '2025-12-03', '2025-12-04', '2025-12-05',
        '2026-01-01', '2026-01-02', '2026-01-03',
        '2026-04-30', '2026-05-01', '2026-05-02',
        '2026-05-29', '2026-05-30', '2026-05-31',
    ]

    // Special fasts
    const specialFasts = {
        '2025-07-15': { type: 'ashura', hijri_month: 1, hijri_day: 9 },
        '2025-07-16': { type: 'ashura', hijri_month: 1, hijri_day: 10 },
        '2026-05-26': { type: 'arafah', hijri_month: 12, hijri_day: 9 },
    }

    // Build fasting map
    const current = new Date(start)
    while (current <= end) {
        const dateStr = current.toISOString().split('T')[0]
        const dayOfWeek = current.getDay()

        // Check fasting periods
        let isFasting = false
        let fastType = null
        let hijriMonth = 0
        let hijriDay = 0

        for (const period of fastingPeriods) {
            if (current >= period.start && current <= period.end) {
                isFasting = true
                fastType = period.type
                hijriMonth = period.hijri_month
                hijriDay = Math.floor((current - period.start) / 86400000) + 1
                break
            }
        }

        // Ayyam al-Bid
        if (!isFasting && ayyamDates.includes(dateStr)) {
            isFasting = true
            fastType = 'ayyam_al_bid'
            hijriMonth = 10
            hijriDay = 13 + ayyamDates.indexOf(dateStr) % 3
        }

        // Special fasts
        if (!isFasting && specialFasts[dateStr]) {
            isFasting = true
            fastType = specialFasts[dateStr].type
            hijriMonth = specialFasts[dateStr].hijri_month
            hijriDay = specialFasts[dateStr].hijri_day
        }

        // Weekly Sunnah (Mon=1, Thu=4)
        if (!isFasting && (dayOfWeek === 1 || dayOfWeek === 4)) {
            isFasting = true
            fastType = 'weekly_sunnah'
        }

        if (isFasting) {
            fastingMap[dateStr] = {
                date: dateStr,
                is_fasting: true,
                fast_type: fastType,
                hijri_month: hijriMonth,
                hijri_day: hijriDay,
            }
        }

        current.setDate(current.getDate() + 1)
    }

    // Generate health data with realistic fasting correlations
    const healthCurrent = new Date(start)
    while (healthCurrent <= end) {
        const dateStr = healthCurrent.toISOString().split('T')[0]
        const isFasting = !!fastingMap[dateStr]
        const isRamadan = fastingMap[dateStr]?.fast_type === 'ramadan'

        // Base values with natural variation
        const noise = () => (Math.random() - 0.5) * 2

        // Resting heart rate — lower on fasting days (realistic ~3-5 bpm difference)
        const baseHR = 62
        const hrFastingBonus = isFasting ? -4 : 0
        const hrRamadanBonus = isRamadan ? -2 : 0
        const hr = Math.round(baseHR + hrFastingBonus + hrRamadanBonus + noise() * 4)

        // Steps — slightly lower on fasting days (less energy)
        const baseSteps = 7800
        const stepsFastingPenalty = isFasting ? -800 : 0
        const steps = Math.round(Math.max(1000,
            baseSteps + stepsFastingPenalty + noise() * 2000
        ))

        // Active calories — correlated with steps
        const calories = Math.round(steps * 0.065 + noise() * 50)

        // Sleep — slightly better on fasting days
        const baseSleep = 6.8
        const sleepFastingBonus = isFasting ? 0.3 : 0
        const sleep = parseFloat(Math.max(4,
            Math.min(10, baseSleep + sleepFastingBonus + noise() * 0.8)
        ).toFixed(1))

        // Push each metric as separate row (matches real API format)
        healthArray.push({ date: dateStr, metric: 'resting_heart_rate', value: hr })
        healthArray.push({ date: dateStr, metric: 'steps', value: steps })
        healthArray.push({ date: dateStr, metric: 'active_calories', value: calories })
        healthArray.push({ date: dateStr, metric: 'sleep', value: sleep })

        healthCurrent.setDate(healthCurrent.getDate() + 1)
    }

    return { fastingMap, healthArray }
}

export const { fastingMap: demoFastingData, healthArray: demoHealthData } = generateDemoData()