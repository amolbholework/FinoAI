interface ScamAwarenessArtProps {
  size?: number
  className?: string
}

/** Spot illustration for the landing page's "Stay safe" band — a shield
 * with a checkmark. Uses warning (the section's own background-gradient
 * accent) for the shield and positive (the app-wide "this is fine/safe"
 * token, same one the privacy strip's checkmarks use below) for the
 * checkmark — never overspend, which is reserved solely for money moving
 * out. Purely decorative (the heading text next to it already carries the
 * meaning), so aria-hidden. */
export function ScamAwarenessArt({ size = 56, className = '' }: ScamAwarenessArtProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 56 56" fill="none" aria-hidden="true" className={className}>
      <path
        d="M28 6l17 6v13c0 12-7.5 19.5-17 24C18.5 44.5 11 37 11 25V12z"
        fill="var(--color-warning-soft)"
        stroke="var(--color-warning)"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
      <path d="M20 27l6 6 11-13" stroke="var(--color-positive)" strokeWidth="2.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
