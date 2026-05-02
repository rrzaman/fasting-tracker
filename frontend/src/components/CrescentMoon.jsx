// JD 2451550.1 = Jan 6 2000, known new moon. Synodic month = 29.53059 d.
function getLunarPhase() {
  const JD = Date.now() / 86400000 + 2440587.5
  const elapsed = ((JD - 2451550.1) % 29.53059 + 29.53059) % 29.53059
  return elapsed / 29.53059  // 0 = new moon, ~0.5 = full moon
}

// Returns an SVG path for the lit portion of the moon.
// Phase 0 = new (dark), 0.25 = first quarter (right half),
// 0.5 = full, 0.75 = last quarter (left half).
function phasePath(phase, R = 18, cx = 25, cy = 25) {
  if (phase < 0.02 || phase > 0.98) return null  // new moon — no lit area
  const top = `${cx},${cy - R}`
  const bot = `${cx},${cy + R}`
  const k  = Math.cos(phase * 2 * Math.PI)  // 1=new, -1=full
  const rx = (Math.abs(k) * R).toFixed(2)

  if (phase < 0.5) {
    // Waxing — right side lit
    return k >= 0
      ? `M ${top} A ${R} ${R} 0 1 1 ${bot} A ${rx} ${R} 0 0 0 ${top} Z`   // crescent
      : `M ${top} A ${R} ${R} 0 1 1 ${bot} A ${rx} ${R} 0 0 1 ${top} Z`   // gibbous
  }
  // Waning — left side lit
  return k <= 0
    ? `M ${top} A ${R} ${R} 0 1 0 ${bot} A ${rx} ${R} 0 0 0 ${top} Z`     // gibbous
    : `M ${top} A ${R} ${R} 0 1 0 ${bot} A ${rx} ${R} 0 0 1 ${top} Z`     // crescent
}

export default function CrescentMoon() {
  const phase = getLunarPhase()
  const path  = phasePath(phase)
  const day   = Math.floor(phase * 29.53) + 1

  return (
    <svg
      width="50"
      height="50"
      viewBox="0 0 50 50"
      className="moon-svg"
      aria-label={`Moon, day ${day} of lunar month`}
    >
      <defs>
        <radialGradient id="moonGrad" cx="40%" cy="35%" r="60%">
          <stop offset="0%"   stopColor="#fef3c7" />
          <stop offset="50%"  stopColor="#f0c040" />
          <stop offset="100%" stopColor="#c9952a" />
        </radialGradient>
      </defs>
      {/* Unlit moon disk */}
      <circle cx="25" cy="25" r="18"
        fill="rgba(5,18,10,0.75)"
        stroke="rgba(240,192,64,0.18)"
        strokeWidth="0.5"
      />
      {/* Lit phase */}
      {path && <path d={path} fill="url(#moonGrad)" />}
    </svg>
  )
}
