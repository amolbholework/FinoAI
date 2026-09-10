interface EmptyHealthDataArtProps {
  size?: number
  className?: string
}

/** Empty-state illustration for "not enough data to compute a health
 * score yet" — a dashed, needle-less version of the HealthGauge arc with a
 * question mark where the score would sit, so it visually rhymes with the
 * real gauge shown once data exists. Purely decorative, aria-hidden. */
export function EmptyHealthDataArt({ size = 140, className = '' }: EmptyHealthDataArtProps) {
  return (
    <svg width={size} height={size * 0.66} viewBox="0 0 160 105" fill="none" aria-hidden="true" className={className}>
      <path
        d="M20 95a60 60 0 01120 0"
        stroke="var(--color-border)"
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray="1 14"
      />
      <circle cx="80" cy="95" r="6" fill="var(--color-card)" stroke="var(--color-muted)" strokeWidth="2" />
      <text x="80" y="70" textAnchor="middle" fontSize="26" fontFamily="var(--font-heading)" fontWeight="700" fill="var(--color-muted)">
        ?
      </text>
    </svg>
  )
}
