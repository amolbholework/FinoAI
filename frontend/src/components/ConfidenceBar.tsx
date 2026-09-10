const LOW_CONFIDENCE_THRESHOLD = 0.7

interface ConfidenceBarProps {
  value: number // 0-1
  className?: string
}

/**
 * Small confidence indicator reused by the CSV preview table and the
 * screenshot review card. Below 0.7 it switches to the coral "needs a
 * look" treatment; at or above it reads as a quiet, confident muted bar.
 */
export function ConfidenceBar({ value, className = '' }: ConfidenceBarProps) {
  const pct = Math.round(value * 100)
  const isLow = value < LOW_CONFIDENCE_THRESHOLD
  const barColor = isLow ? 'var(--color-overspend)' : 'var(--color-positive)'

  return (
    <div className={`flex items-center justify-end gap-2 ${className}`}>
      <div className="h-[5px] w-11 overflow-hidden rounded-full bg-hairline">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: barColor }} />
      </div>
      <span className="tabular-nums text-xs" style={{ color: isLow ? 'var(--color-overspend)' : 'var(--color-muted)' }}>
        {pct}%
      </span>
    </div>
  )
}
