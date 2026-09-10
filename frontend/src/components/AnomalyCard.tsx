import { motion } from 'framer-motion'
import { formatMoney } from '../lib/format'

interface AnomalyCardProps {
  title: string
  description: string
  amountMinor: number
  currency: string
  severity: 'high' | 'medium'
}

const SEVERITY_STYLE = {
  high: { border: 'var(--color-overspend)', bg: 'var(--color-overspend-soft)', text: 'var(--color-overspend-ink)' },
  medium: { border: 'var(--color-warning)', bg: 'var(--color-warning-soft)', text: 'var(--color-warning-ink)' },
}

/** One flagged, out-of-the-ordinary transaction or category-month, presented
 * inline on the dashboard rather than requiring a drill-down into the
 * anomalies endpoint to notice. Plain-language description does the
 * explaining; the z-score that drove the flag stays a backend concern. */
export function AnomalyCard({ title, description, amountMinor, currency, severity }: AnomalyCardProps) {
  const style = SEVERITY_STYLE[severity]
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border p-3"
      style={{ borderColor: `${style.border}33`, background: style.bg }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold" style={{ color: style.text }}>
            {title}
          </p>
          <p className="mt-0.5 text-xs text-secondary">{description}</p>
        </div>
        <p className="money shrink-0 text-sm font-semibold" style={{ color: style.text }}>
          {formatMoney(amountMinor, currency)}
        </p>
      </div>
    </motion.div>
  )
}
