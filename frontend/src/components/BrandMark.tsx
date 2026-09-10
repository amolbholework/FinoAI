interface BrandMarkProps {
  /** Wordmark height in px — the glyph and type scale together from this. */
  size?: number
  className?: string
  /** Glyph only, no "FinPilot AI" text — for tight spaces like a mini sidebar poster. */
  iconOnly?: boolean
}

/**
 * The FinPilot wordmark: gradient glyph + "FinPilot" in Sora, "AI" set apart
 * in the muted tone. No image asset exists for this product, so the mark is
 * built as type + inline SVG rather than an <img> — it stays crisp at any
 * size and needs no separate export pipeline.
 */
export function BrandMark({ size = 22, className = '', iconOnly = false }: BrandMarkProps) {
  const glyphId = `fp-glyph-grad-${size}`
  return (
    <span className={`inline-flex items-center gap-2 ${className}`} style={{ height: size }}>
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id={glyphId} x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="var(--color-cyan)" />
            <stop offset="1" stopColor="var(--color-primary)" />
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="28" height="28" rx="9" fill={`url(#${glyphId})`} />
        <path d="M12 22 V13.5 C12 10.5 14 9 17 9 H20" stroke="#FFFFFF" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 16.5 H18" stroke="#FFFFFF" strokeWidth="2.6" strokeLinecap="round" />
      </svg>
      {!iconOnly && (
        <span
          className="font-heading font-bold text-heading"
          style={{ fontSize: size * 0.68, letterSpacing: '-0.01em', lineHeight: 1 }}
        >
          FinPilot
          <span className="text-muted font-semibold" style={{ marginLeft: size * 0.18 }}>
            AI
          </span>
        </span>
      )}
    </span>
  )
}
