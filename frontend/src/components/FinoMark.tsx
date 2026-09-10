interface FinoMarkProps {
  size?: number
  className?: string
}

/** Fino's avatar — same cyan→indigo gradient family as BrandMark, but a
 * distinct glyph (a spark, not the "F" monogram) so Fino reads as FinPilot's
 * assistant rather than a restyled logo. */
export function FinoMark({ size = 28, className = '' }: FinoMarkProps) {
  const gradId = `fino-glyph-grad-${size}`
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true" className={className}>
      <defs>
        <linearGradient id={gradId} x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--color-cyan)" />
          <stop offset="1" stopColor="var(--color-primary)" />
        </linearGradient>
      </defs>
      <circle cx="16" cy="16" r="14" fill={`url(#${gradId})`} />
      <path
        d="M16 8.5l2.1 4.6 4.9.6-3.6 3.4.9 4.9L16 19.4l-4.3 2.6.9-4.9-3.6-3.4 4.9-.6z"
        fill="#FFFFFF"
      />
    </svg>
  )
}
