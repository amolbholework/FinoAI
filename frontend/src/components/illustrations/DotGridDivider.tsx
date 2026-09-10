interface DotGridDividerProps {
  className?: string
}

/** A quiet dot-grid texture for section backgrounds — never competes with
 * charts or copy, just enough to keep a plain-canvas section from feeling
 * flat. Built as a tiled SVG <pattern> so it stays lean regardless of the
 * section's size. Purely decorative, aria-hidden. */
export function DotGridDivider({ className = '' }: DotGridDividerProps) {
  return (
    <svg width="100%" height="100%" aria-hidden="true" className={className} preserveAspectRatio="none">
      <defs>
        <pattern id="dot-grid-divider" width="28" height="28" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.4" fill="var(--color-border)" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#dot-grid-divider)" opacity="0.6" />
    </svg>
  )
}
