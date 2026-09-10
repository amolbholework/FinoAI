interface EmptyForecastArtProps {
  size?: number
  className?: string
}

/** Empty-state illustration for "no forecast data yet" — a short solid
 * history line trailing into a dashed, band-less continuation, echoing the
 * real ForecastPage chart's history/predicted split but with the
 * confidence band left unfilled to signal "nothing computed yet."
 * Library component: not currently wired into ForecastPage, which always
 * has at least a cold-start average to show once any transaction exists.
 * Purely decorative, aria-hidden. */
export function EmptyForecastArt({ size = 120, className = '' }: EmptyForecastArtProps) {
  return (
    <svg width={size} height={size * 0.6} viewBox="0 0 160 96" fill="none" aria-hidden="true" className={className}>
      <line x1="8" y1="30" x2="8" y2="80" stroke="var(--color-hairline)" strokeWidth="1" />
      <line x1="8" y1="80" x2="152" y2="80" stroke="var(--color-hairline)" strokeWidth="1" />
      <path d="M8 68 C24 64 34 58 48 52 C58 48 62 46 70 42" stroke="var(--color-primary)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <circle cx="70" cy="42" r="3.5" fill="var(--color-primary)" />
      <path
        d="M70 42 C90 38 100 40 118 34 C130 30 140 28 152 22"
        stroke="var(--color-border)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="1 8"
        fill="none"
      />
    </svg>
  )
}
