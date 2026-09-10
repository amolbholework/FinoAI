interface FinoMascotProps {
  size?: number
  className?: string
}

/** A fuller version of Fino than FinoMark (which is tuned for small,
 * frequent placements like the launcher button) — same cyan→indigo
 * gradient family and the same four-point sparkle as its antenna tip, but
 * detailed enough to hold up at 96px for the chat empty state, while still
 * reading cleanly down at 32px. Meaningful (it *is* Fino, not decoration),
 * so it gets a title/role rather than aria-hidden. */
export function FinoMascot({ size = 96, className = '' }: FinoMascotProps) {
  const gradId = `fino-mascot-grad-${size}`
  return (
    <svg width={size} height={size} viewBox="0 0 96 96" fill="none" role="img" className={className}>
      <title>Fino, the FinPilot AI assistant</title>
      <defs>
        <linearGradient id={gradId} x1="12" y1="12" x2="84" y2="84" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--color-cyan)" />
          <stop offset="1" stopColor="var(--color-primary)" />
        </linearGradient>
      </defs>
      <circle cx="48" cy="50" r="38" fill={`url(#${gradId})`} />
      <rect x="26" y="38" width="44" height="26" rx="13" fill="white" />
      <circle cx="38" cy="51" r="4.4" fill="var(--color-primary)" />
      <circle cx="58" cy="51" r="4.4" fill="var(--color-primary)" />
      <path d="M48 12v8" stroke={`url(#${gradId})`} strokeWidth="4" strokeLinecap="round" />
      <path d="M48 6l3.2 7 7 3.2-7 3.2-3.2 7-3.2-7-7-3.2 7-3.2z" fill="var(--color-mesh-gold)" />
    </svg>
  )
}
