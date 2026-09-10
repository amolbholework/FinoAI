interface MutualFundsArtProps {
  size?: number
  className?: string
}

/** Section art for mutual-fund education content — a basket holding
 * several small differently-colored shapes, standing in for "many
 * holdings pooled together" without depicting any real fund, ticker, or
 * return figure. Uses the categorical chart-1..4 tokens (the same ones
 * reserved for "the Nth series, no semantic meaning") rather than any of
 * the reserved-meaning tokens, since this is deliberately generic.
 * Library component: there is no Mutual Funds Sahi Hai page in the app
 * yet, so this isn't wired anywhere — built so it's ready whenever that
 * surface exists. Purely decorative, aria-hidden. */
export function MutualFundsArt({ size = 120, className = '' }: MutualFundsArtProps) {
  return (
    <svg width={size} height={size * 0.75} viewBox="0 0 160 120" fill="none" aria-hidden="true" className={className}>
      <path
        d="M28 52h104l-10 44a10 10 0 01-9.8 8H47.8a10 10 0 01-9.8-8z"
        fill="var(--color-hairline)"
        stroke="var(--color-border)"
        strokeWidth="1.5"
      />
      <path d="M28 52l12-24h80l12 24" stroke="var(--color-border)" strokeWidth="1.5" fill="none" strokeLinejoin="round" />
      <circle cx="62" cy="40" r="9" fill="var(--color-chart-1)" />
      <rect x="82" y="32" width="16" height="16" rx="4" fill="var(--color-chart-3)" />
      <path d="M108 46l8-15 8 15z" fill="var(--color-chart-5)" />
    </svg>
  )
}
