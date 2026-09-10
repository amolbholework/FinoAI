/** Adapted from src/assets/art/health-gauge.svg — same geometry, needle
 * rotated live from the real score (rotate = score * 1.8deg, per the
 * source file's own comment: 0 -> 0deg, 50 -> 90deg, 100 -> 180deg), and
 * recolored onto our token palette instead of the source's placeholder
 * --fp-* variables. The four band arcs line up with the four score bands. */
export function HealthGauge({ score }: { score: number | null }) {
  const angle = score != null ? score * 1.8 : 0

  return (
    <svg viewBox="0 0 320 210" width="100%" role="img" aria-label={score != null ? `Health score gauge, ${score} out of 100` : 'Health score gauge, not enough data yet'}>
      <g fill="none" strokeWidth="22" strokeLinecap="butt">
        <path d="M50 170 A110 110 0 0 1 82.2 92.2" stroke="var(--color-muted)" strokeOpacity=".45" />
        <path d="M82.2 92.2 A110 110 0 0 1 160 60" stroke="var(--color-warning)" strokeOpacity=".55" />
        <path d="M160 60 A110 110 0 0 1 237.8 92.2" stroke="var(--color-positive)" strokeOpacity=".7" />
        <path d="M237.8 92.2 A110 110 0 0 1 270 170" stroke="var(--color-primary)" strokeOpacity=".85" />
      </g>

      {score != null && (
        <g transform={`rotate(${angle} 160 170)`}>
          <polygon points="68,170 160,163.5 160,176.5" fill="var(--color-heading)" />
        </g>
      )}
      <circle cx="160" cy="170" r="10" fill="var(--color-card)" stroke="var(--color-heading)" strokeWidth="3" />

      <g stroke="var(--color-heading)" strokeOpacity=".25" strokeWidth="2" strokeLinecap="round">
        <line x1="34" y1="170" x2="24" y2="170" />
        <line x1="286" y1="170" x2="296" y2="170" />
      </g>
    </svg>
  )
}
