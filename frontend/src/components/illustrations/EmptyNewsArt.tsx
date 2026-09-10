interface EmptyNewsArtProps {
  size?: number
  className?: string
}

/** Empty-state illustration for "no news available" — a small stack of
 * article cards with placeholder headline/body lines. Library component:
 * there is no Finance News page in the app yet, so this isn't wired
 * anywhere — built so it's ready whenever that surface exists. Purely
 * decorative, aria-hidden. */
export function EmptyNewsArt({ size = 120, className = '' }: EmptyNewsArtProps) {
  return (
    <svg width={size} height={size * 0.75} viewBox="0 0 160 120" fill="none" aria-hidden="true" className={className}>
      <rect x="20" y="18" width="90" height="70" rx="10" fill="var(--color-hairline)" />
      <rect x="34" y="32" width="90" height="70" rx="10" fill="var(--color-card)" stroke="var(--color-border)" strokeWidth="1.5" />
      <rect x="48" y="46" width="62" height="7" rx="3.5" fill="var(--color-heading)" opacity="0.7" />
      <rect x="48" y="60" width="62" height="4.5" rx="2.25" fill="var(--color-muted)" opacity="0.5" />
      <rect x="48" y="70" width="46" height="4.5" rx="2.25" fill="var(--color-muted)" opacity="0.5" />
      <rect x="48" y="80" width="52" height="4.5" rx="2.25" fill="var(--color-muted)" opacity="0.5" />
      <circle cx="126" cy="30" r="12" fill="var(--color-cyan-soft)" />
      <path d="M121 30l3.5 3.5L131 26" stroke="var(--color-cyan-ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
