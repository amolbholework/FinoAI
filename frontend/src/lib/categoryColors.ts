// Deterministic pill color per category name, cycling through the design
// system's soft/ink token pairs. New user-created categories still get a
// sensible color without needing a hardcoded entry per name.
const PALETTE: Array<{ bg: string; ink: string }> = [
  { bg: 'var(--color-primary-soft)', ink: 'var(--color-primary)' },
  { bg: 'var(--color-cyan-soft)', ink: 'var(--color-cyan-ink)' },
  { bg: 'var(--color-positive-soft)', ink: 'var(--color-positive-ink)' },
  { bg: 'var(--color-overspend-soft)', ink: 'var(--color-overspend-ink)' },
  { bg: 'var(--color-warning-soft)', ink: 'var(--color-warning-ink)' },
]

const FIXED: Record<string, { bg: string; ink: string }> = {
  Income: { bg: 'var(--color-positive-soft)', ink: 'var(--color-positive-ink)' },
  Food: { bg: 'var(--color-overspend-soft)', ink: 'var(--color-overspend-ink)' },
  Other: { bg: 'var(--color-hairline)', ink: 'var(--color-secondary)' },
}

export function categoryPillColors(name: string | null | undefined): { bg: string; ink: string } {
  if (!name) return { bg: 'var(--color-hairline)', ink: 'var(--color-muted)' }
  if (FIXED[name]) return FIXED[name]

  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
}
