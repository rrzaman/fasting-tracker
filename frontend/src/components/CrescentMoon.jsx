export default function CrescentMoon() {
  return (
    <svg
      width="50"
      height="50"
      viewBox="0 0 50 50"
      style={{
        display: 'block',
        margin: '0 auto 0.75rem',
        filter: 'drop-shadow(0 0 10px rgba(240, 192, 64, 0.7))',
      }}
      aria-label="Crescent moon"
    >
      <defs>
        <radialGradient id="moonGrad" cx="40%" cy="35%" r="60%">
          <stop offset="0%"   stopColor="#fef3c7" />
          <stop offset="50%"  stopColor="#f0c040" />
          <stop offset="100%" stopColor="#c9952a" />
        </radialGradient>
        <mask id="crescentMask">
          {/* Full white circle — visible area */}
          <circle cx="25" cy="25" r="20" fill="white" />
          {/* Black offset circle — cuts out the crescent */}
          <circle cx="32" cy="22" r="16" fill="black" />
        </mask>
      </defs>
      <circle
        cx="25"
        cy="25"
        r="20"
        fill="url(#moonGrad)"
        mask="url(#crescentMask)"
      />
    </svg>
  )
}