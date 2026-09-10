import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { formatMoney } from '../lib/format'
import { Skeleton } from './Skeleton'
import type { DailyBurnPoint } from '../lib/types'

interface BurnRateStripProps {
  dailyBurn: DailyBurnPoint[] | null
  daysInMonth: number
  budgetLimitMinor: number | null
  currency: string
}

const WIDTH = 600
const HEIGHT = 88
const PAD_X = 4
const PAD_Y = 12

/** The dashboard's signature element: a full-width cumulative spend line
 * across the days of the current month, with the monthly budget limit drawn
 * as a flat reference line so "am I ahead of pace" is a single glance —
 * where the solid line sits relative to the dashed one — rather than a
 * number the user has to do math on. Deliberately plain-SVG (not recharts)
 * so its exact shape and the "today" marker are easy to hand-tune. */
export function BurnRateStrip({ dailyBurn, daysInMonth, budgetLimitMinor, currency }: BurnRateStripProps) {
  const geometry = useMemo(() => {
    if (!dailyBurn || dailyBurn.length === 0) return null

    const todaySpend = dailyBurn[dailyBurn.length - 1].cumulative_spend_minor
    const maxValue = Math.max(todaySpend, budgetLimitMinor ?? 0, 1)

    const xFor = (day: number) => PAD_X + ((day - 1) / Math.max(daysInMonth - 1, 1)) * (WIDTH - PAD_X * 2)
    const yFor = (value: number) => HEIGHT - PAD_Y - (value / maxValue) * (HEIGHT - PAD_Y * 2)

    const linePoints = dailyBurn.map((p) => [xFor(p.day), yFor(p.cumulative_spend_minor)] as const)
    const path = linePoints.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
    const areaPath = `${path} L${linePoints[linePoints.length - 1][0].toFixed(1)},${HEIGHT - PAD_Y} L${linePoints[0][0].toFixed(1)},${HEIGHT - PAD_Y} Z`

    const [todayX, todayY] = linePoints[linePoints.length - 1]
    const budgetY = budgetLimitMinor != null ? yFor(budgetLimitMinor) : null
    const isOverPace = budgetLimitMinor != null && todaySpend > (budgetLimitMinor / daysInMonth) * dailyBurn.length

    return { path, areaPath, todayX, todayY, budgetY, todaySpend, isOverPace }
  }, [dailyBurn, daysInMonth, budgetLimitMinor])

  if (!dailyBurn) {
    return <Skeleton className="h-[88px] w-full" />
  }

  if (!geometry) {
    return <p className="text-sm text-muted">No spend recorded yet this month.</p>
  }

  const lineColor = geometry.isOverPace ? 'var(--color-overspend)' : 'var(--color-primary)'

  return (
    <div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" preserveAspectRatio="none" role="img" aria-label={`Cumulative spend this month, currently ${formatMoney(geometry.todaySpend, currency)}`}>
        {geometry.budgetY != null && (
          <line x1={PAD_X} y1={geometry.budgetY} x2={WIDTH - PAD_X} y2={geometry.budgetY} stroke="var(--color-muted)" strokeWidth="1" strokeDasharray="4 4" />
        )}
        <motion.path
          d={geometry.areaPath}
          fill={lineColor}
          fillOpacity={0.08}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        />
        <motion.path
          d={geometry.path}
          fill="none"
          stroke={lineColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
        <circle cx={geometry.todayX} cy={geometry.todayY} r="4" fill={lineColor} />
        <circle cx={geometry.todayX} cy={geometry.todayY} r="8" fill={lineColor} fillOpacity={0.18} />
      </svg>
      <div className="mt-1 flex items-center justify-between text-xs text-muted">
        <span>Day 1</span>
        {budgetLimitMinor != null && <span>Budget: {formatMoney(budgetLimitMinor, currency)}</span>}
        <span>Day {daysInMonth}</span>
      </div>
    </div>
  )
}
