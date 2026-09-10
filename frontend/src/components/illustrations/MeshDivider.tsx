interface MeshDividerProps {
  className?: string
}

/** A quiet, static two-tone gradient wash for a section background — the
 * same brand hues as .hero-mesh (cyan/primary) but static and much lower
 * opacity, so it reads as a section backdrop rather than a second hero.
 * Purely decorative, aria-hidden. */
export function MeshDivider({ className = '' }: MeshDividerProps) {
  return (
    <div
      aria-hidden="true"
      className={className}
      style={{
        background:
          'radial-gradient(circle at 12% 15%, color-mix(in srgb, var(--color-cyan) 12%, transparent), transparent 55%), ' +
          'radial-gradient(circle at 88% 85%, color-mix(in srgb, var(--color-primary) 10%, transparent), transparent 50%)',
      }}
    />
  )
}
