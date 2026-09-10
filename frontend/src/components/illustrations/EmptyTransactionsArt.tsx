interface EmptyTransactionsArtProps {
  size?: number
  className?: string
}

/** Empty-state illustration for "no transactions yet" — a dashed upload
 * frame around a small ledger sheet, with an upload-arrow badge overlapping
 * the bottom edge. Purely decorative next to the empty state's own heading
 * and copy, so aria-hidden. */
export function EmptyTransactionsArt({ size = 120, className = '' }: EmptyTransactionsArtProps) {
  return (
    <svg width={size} height={size * 0.75} viewBox="0 0 160 120" fill="none" aria-hidden="true" className={className}>
      <rect x="8" y="6" width="144" height="100" rx="14" stroke="var(--color-border)" strokeWidth="2" strokeDasharray="6 6" />
      <g transform="translate(46 22)">
        <rect width="68" height="60" rx="8" fill="var(--color-primary-soft)" stroke="var(--color-primary-border)" strokeWidth="1.5" />
        <rect x="12" y="14" width="34" height="5" rx="2.5" fill="var(--color-primary)" opacity="0.7" />
        <rect x="12" y="28" width="44" height="4" rx="2" fill="var(--color-muted)" opacity="0.55" />
        <rect x="12" y="38" width="30" height="4" rx="2" fill="var(--color-muted)" opacity="0.55" />
      </g>
      <g transform="translate(80 84)">
        <circle r="18" fill="var(--color-primary)" />
        <path d="M0 7v-13M-6 -1l6 -7 6 7" stroke="white" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  )
}
