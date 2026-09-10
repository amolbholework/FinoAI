import { motion } from 'framer-motion'
import { formatMoney } from '../lib/format'
import { Skeleton } from './Skeleton'

const CHART_COLORS = [
  'var(--color-chart-1)',
  'var(--color-chart-2)',
  'var(--color-chart-3)',
  'var(--color-chart-4)',
  'var(--color-chart-5)',
  'var(--color-chart-6)',
  'var(--color-chart-7)',
  'var(--color-chart-8)',
]

interface CategoryBreakdownProps {
  data: Record<string, number> | null
  currency: string
  onCategoryClick?: (category: string) => void
}

export function CategoryBreakdown({ data, currency, onCategoryClick }: CategoryBreakdownProps) {
  if (!data) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-6 w-full" />
        ))}
      </div>
    )
  }

  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = entries.length ? entries[0][1] : 1

  if (entries.length === 0) {
    return <p className="text-sm text-muted">No spend recorded yet.</p>
  }

  return (
    <div className="space-y-3">
      {entries.map(([category, amount], i) => {
        const row = (
          <>
            <div className="mb-1 flex items-baseline justify-between text-sm">
              <span className="font-medium text-heading">{category}</span>
              <span className="money text-secondary">{formatMoney(amount, currency)}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-hairline">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                initial={{ width: 0 }}
                animate={{ width: `${(amount / max) * 100}%` }}
                transition={{ duration: 0.6, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </>
        )
        return onCategoryClick ? (
          <button
            key={category}
            type="button"
            onClick={() => onCategoryClick(category)}
            className="block w-full rounded-lg text-left transition hover:opacity-80"
          >
            {row}
          </button>
        ) : (
          <div key={category}>{row}</div>
        )
      })}
    </div>
  )
}
