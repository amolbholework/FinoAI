interface EmptyAdviceArtProps {
  size?: number
  className?: string
}

/** Empty-state illustration for "no recommendations yet" — a speech
 * bubble with placeholder lines and a small sparkle, using the AI accent
 * token so it reads as the same family as the AI-marked content elsewhere
 * on the Advice page. Purely decorative, aria-hidden. */
export function EmptyAdviceArt({ size = 120, className = '' }: EmptyAdviceArtProps) {
  return (
    <svg width={size} height={size * 0.75} viewBox="0 0 160 120" fill="none" aria-hidden="true" className={className}>
      <path
        d="M20 20h100a12 12 0 0112 12v46a12 12 0 01-12 12H62l-22 18v-18H20a12 12 0 01-12-12V32a12 12 0 0112-12z"
        fill="var(--color-ai-soft)"
        stroke="var(--color-ai)"
        strokeOpacity="0.4"
        strokeWidth="1.5"
      />
      <rect x="32" y="42" width="66" height="6" rx="3" fill="var(--color-ai)" opacity="0.55" />
      <rect x="32" y="56" width="50" height="5" rx="2.5" fill="var(--color-muted)" opacity="0.45" />
      <rect x="32" y="68" width="58" height="5" rx="2.5" fill="var(--color-muted)" opacity="0.45" />
      <path d="M130 18l3.2 7 7 3.2-7 3.2-3.2 7-3.2-7-7-3.2 7-3.2z" fill="var(--color-ai)" opacity="0.7" />
    </svg>
  )
}
