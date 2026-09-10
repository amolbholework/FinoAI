interface MarketEducationArtProps {
  size?: number
  className?: string
}

/** Section art for market-education content — an open book with a small
 * rising-trend line across its pages, pairing "learning" with "markets"
 * without depicting any real chart or security. Library component: there
 * is no Market Education page in the app yet, so this isn't wired
 * anywhere — built so it's ready whenever that surface exists. Purely
 * decorative, aria-hidden. */
export function MarketEducationArt({ size = 120, className = '' }: MarketEducationArtProps) {
  return (
    <svg width={size} height={size * 0.75} viewBox="0 0 160 120" fill="none" aria-hidden="true" className={className}>
      <path
        d="M18 30c14-8 32-8 42 0v62c-10-8-28-8-42 0z"
        fill="var(--color-primary-soft)"
        stroke="var(--color-primary-border)"
        strokeWidth="1.5"
      />
      <path
        d="M142 30c-14-8-32-8-42 0v62c10-8 28-8 42 0z"
        fill="var(--color-cyan-soft)"
        stroke="var(--color-primary-border)"
        strokeWidth="1.5"
      />
      <path
        d="M30 52c8 6 18 8 24 8"
        stroke="var(--color-primary)"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.5"
      />
      <path
        d="M30 66c8 5 18 6 24 6"
        stroke="var(--color-primary)"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.5"
      />
      <path
        d="M50 44 C64 56 72 34 80 44 C90 56 98 30 110 40"
        stroke="var(--color-positive)"
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="110" cy="40" r="3.5" fill="var(--color-positive)" />
    </svg>
  )
}
