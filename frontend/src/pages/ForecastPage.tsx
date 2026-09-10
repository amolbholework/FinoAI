import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatMoney, formatMonth } from '../lib/format'
import { ChartCaption } from '../components/ChartCaption'
import { Skeleton } from '../components/Skeleton'
import type { Category, HorizonForecastResponse } from '../lib/types'

const CHART_WIDTH = 700
const CHART_HEIGHT = 280
const PLOT_TOP = 20
const PLOT_BOTTOM = 245

const HORIZON_OPTIONS = [1, 3, 6] as const

function buildGeometry(history: { month: string; totalMinor: number }[], predicted: HorizonForecastResponse['months']) {
  const historyPoints = history.map((m) => m.totalMinor)
  const predictedPoints = predicted.map((m) => m.predicted_minor)
  const highPoints = predicted.map((m) => m.high_minor)
  const lowPoints = predicted.map((m) => m.low_minor)
  const all = [...historyPoints, ...predictedPoints, ...highPoints, ...lowPoints, 1]
  const min = Math.min(...all) * 0.92
  const max = Math.max(...all) * 1.05
  const range = max - min || 1

  const totalPoints = history.length + predicted.length
  const stepX = totalPoints > 1 ? CHART_WIDTH / (totalPoints - 1) : CHART_WIDTH
  const toY = (v: number) => PLOT_BOTTOM - ((v - min) / range) * (PLOT_BOTTOM - PLOT_TOP)
  const toX = (i: number) => i * stepX

  const historyXY = historyPoints.map((v, i) => [toX(i), toY(v)] as const)
  const todayIndex = history.length - 1
  const predictedXY = predictedPoints.map((v, i) => [toX(todayIndex + 1 + i), toY(v)] as const)
  const highXY = highPoints.map((v, i) => [toX(todayIndex + 1 + i), toY(v)] as const)
  const lowXY = lowPoints.map((v, i) => [toX(todayIndex + 1 + i), toY(v)] as const)

  const line = (pts: readonly (readonly [number, number])[]) =>
    pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')

  const historyPath = line(historyXY)
  const anchor = historyXY.length ? historyXY[historyXY.length - 1] : ([0, toY(0)] as const)
  const predictedPath = line([anchor, ...predictedXY])

  const bandTop = [anchor, ...highXY]
  const bandBottom = [anchor, ...lowXY].reverse()
  const bandPath = predicted.length ? `${line(bandTop)} L${line(bandBottom).slice(1)} Z` : ''

  return {
    historyPath,
    predictedPath,
    bandPath,
    todayX: anchor[0],
    todayY: anchor[1],
    months: [...history.map((m) => m.month), ...predicted.map((m) => m.month)],
  }
}

export function ForecastPage() {
  const currency = useCurrency()
  const [horizon, setHorizon] = useState<(typeof HORIZON_OPTIONS)[number]>(3)
  const [monthlyTotals, setMonthlyTotals] = useState<Record<string, number> | null>(null)
  const [horizonData, setHorizonData] = useState<HorizonForecastResponse | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState(false)

  useEffect(() => {
    api.get('/analysis/monthly-totals').then((res) => setMonthlyTotals(res.data))
    api.get<Category[]>('/categories').then((res) => setCategories(res.data))
  }, [])

  useEffect(() => {
    setError(false)
    api
      .get<HorizonForecastResponse>('/forecasts/horizon', { params: { months: horizon } })
      .then((res) => setHorizonData(res.data))
      .catch(() => setError(true))
  }, [horizon])

  const history = useMemo(() => {
    if (!monthlyTotals) return []
    // Last 6 months of history keeps the chart legible next to a 6-month forecast.
    return Object.entries(monthlyTotals)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-6)
      .map(([month, totalMinor]) => ({ month, totalMinor }))
  }, [monthlyTotals])

  const geometry = useMemo(() => {
    if (!horizonData) return null
    return buildGeometry(history, horizonData.months)
  }, [history, horizonData])

  const predictedTotalMinor = horizonData?.months.reduce((sum, m) => sum + m.predicted_minor, 0) ?? 0
  const isLoading = monthlyTotals === null || horizonData === null

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-h2 font-bold text-heading">Forecast</h1>
          <p className="mt-1.5 text-sm text-muted">Projected spending, with a confidence range instead of a single number</p>
        </div>
        <div className="flex gap-1 rounded-lg border border-border bg-card p-1">
          {HORIZON_OPTIONS.map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                horizon === h ? 'bg-primary text-white' : 'text-secondary hover:bg-hairline'
              }`}
            >
              {h} {h === 1 ? 'month' : 'months'}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="card-lifted px-6 py-16 text-center text-sm text-muted">
          Couldn't load your forecast. <button onClick={() => setHorizon((h) => h)} className="text-primary hover:underline">Try again</button>
        </div>
      ) : isLoading ? (
        <Skeleton className="h-72 w-full rounded-2xl" />
      ) : (
        <>
          {horizonData!.model_used === 'average_fallback' && (
            <div className="mb-6 rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] px-4 py-3 text-sm text-[var(--color-warning-ink)]">
              Not enough transaction history yet ({horizonData!.history_months} {horizonData!.history_months === 1 ? 'month' : 'months'}) for a
              trend-based forecast — this is a simple average of what's there so far, shown with a wide confidence range on purpose.
            </div>
          )}

          <div className="mb-11 grid grid-cols-1 items-start gap-5 lg:grid-cols-[2fr_1fr]">
            <div className="card-lifted p-8">
              <div className="mb-6 flex flex-wrap items-start justify-between gap-x-4 gap-y-3">
                <div>
                  <div className="mb-1.5 text-[12.5px] text-muted">
                    Predicted total spend, next {horizon === 1 ? 'month' : `${horizon} months`}
                  </div>
                  <div className="font-heading text-h2 font-bold tracking-tight text-heading tabular-nums">
                    {formatMoney(predictedTotalMinor, currency)}
                  </div>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                  <Legend swatch="dot" color="var(--color-primary)" label="History" />
                  <Legend swatch="dot" color="var(--color-cyan)" label="Predicted" />
                  <Legend swatch="bar" color="color-mix(in srgb, var(--color-cyan) 20%, transparent)" label="Confidence range" />
                </div>
              </div>

              <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} width="100%" height="280" style={{ overflow: 'visible' }} role="img" aria-label={`Spending history and a ${horizon}-month forecast, predicted total ${formatMoney(predictedTotalMinor, currency)}`}>
                <line x1="0" y1="30" x2={CHART_WIDTH} y2="30" stroke="var(--color-hairline)" strokeWidth="1" />
                <line x1="0" y1="95" x2={CHART_WIDTH} y2="95" stroke="var(--color-hairline)" strokeWidth="1" />
                <line x1="0" y1="160" x2={CHART_WIDTH} y2="160" stroke="var(--color-hairline)" strokeWidth="1" />
                <line x1="0" y1="225" x2={CHART_WIDTH} y2="225" stroke="var(--color-hairline)" strokeWidth="1" />
                <line
                  x1={geometry!.todayX}
                  y1="0"
                  x2={geometry!.todayX}
                  y2={PLOT_BOTTOM}
                  stroke="var(--color-border)"
                  strokeWidth="1.5"
                  strokeDasharray="4,4"
                />
                <text x={geometry!.todayX + 6} y="16" fontSize="11" fill="var(--color-muted)">
                  Today
                </text>

                <path d={geometry!.bandPath} fill="var(--color-cyan)" opacity="0.18" />
                <path d={geometry!.historyPath} fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" />
                <path d={geometry!.predictedPath} fill="none" stroke="var(--color-cyan)" strokeWidth="3" strokeLinecap="round" />
                <circle cx={geometry!.todayX} cy={geometry!.todayY} r="5" fill="var(--color-primary)" />
              </svg>
              <div className="mt-2 flex justify-between px-1 text-xs text-muted">
                {geometry!.months.map((m, i) => (
                  <span key={`${m}-${i}`}>{formatMonth(m).slice(0, 3)}</span>
                ))}
              </div>
              <ChartCaption>
                The shaded band is the range the model expects actual spend to fall in — wider means less confident. Based on{' '}
                {horizonData!.history_months} {horizonData!.history_months === 1 ? 'month' : 'months'} of history using the{' '}
                {horizonData!.model_used === 'prophet' ? 'trend model' : 'simple average'}.
              </ChartCaption>
            </div>

            <div className="card-lifted p-7">
              <div className="font-heading mb-1.5 text-[17px] font-semibold text-heading">Biggest movers</div>
              <div className="mb-4.5 text-[12.5px] text-muted">Categories driving next month's change</div>
              {horizonData!.category_drivers.length === 0 ? (
                <p className="text-sm text-muted">Not enough category history yet.</p>
              ) : (
                <div className="flex flex-col gap-4.5">
                  {horizonData!.category_drivers.map((d) => {
                    const categoryId = categories.find((c) => c.name === d.category)?.id
                    return (
                      <Link
                        key={d.category}
                        to={categoryId ? `/transactions?category_id=${categoryId}` : '/transactions'}
                        className="flex items-center justify-between rounded-lg py-1 transition hover:opacity-80"
                      >
                        <div>
                          <div className="mb-0.5 text-[13.5px] font-medium text-body">{d.category}</div>
                          <div
                            className="money text-xs font-semibold"
                            style={{ color: d.delta_minor >= 0 ? 'var(--color-overspend)' : 'var(--color-positive)' }}
                          >
                            {d.delta_minor >= 0 ? '+' : ''}
                            {formatMoney(d.delta_minor, currency)}
                          </div>
                        </div>
                        <div className="money text-right text-xs text-muted">{formatMoney(d.predicted_next_month_minor, currency)}</div>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="mb-11 grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div className="card p-6">
              <div className="font-heading mb-3 text-[16px] font-semibold text-heading">Last month's accuracy</div>
              {horizonData!.accuracy ? (
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-secondary">Predicted</span>
                    <span className="money text-heading">{formatMoney(horizonData!.accuracy.predicted_minor, currency)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary">Actual</span>
                    <span className="money text-heading">{formatMoney(horizonData!.accuracy.actual_minor, currency)}</span>
                  </div>
                  <div className="flex justify-between border-t border-hairline pt-1.5">
                    <span className="text-secondary">Off by</span>
                    <span className="money font-medium text-heading">
                      {formatMoney(horizonData!.accuracy.error_minor, currency)}
                      {horizonData!.accuracy.error_pct !== null && ` (${horizonData!.accuracy.error_pct.toFixed(1)}%)`}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted">No prior forecast to check yet — this fills in after a full month has passed.</p>
              )}
            </div>

            <div className="card p-6">
              <div className="font-heading mb-3 text-[16px] font-semibold text-heading">How this forecast works</div>
              <p className="text-sm leading-relaxed text-secondary">
                {horizonData!.model_used === 'prophet'
                  ? `Built from ${horizonData!.history_months} months of your transaction history using a trend model that looks for month-to-month patterns. `
                  : `With only ${horizonData!.history_months} ${horizonData!.history_months === 1 ? 'month' : 'months'} of history, there isn't enough data for a trend model — this is a plain average instead. `}
                {horizonData!.is_low_confidence && 'The confidence range is wide because there is not much history to learn from yet — it will narrow as more months come in.'}
              </p>
              <Link to="/what-if" className="mt-4 inline-block text-sm font-medium text-primary hover:underline">
                Test this in What-If →
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Legend({ swatch, color, label }: { swatch: 'dot' | 'bar'; color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-muted">
      <span
        className={swatch === 'dot' ? 'inline-block h-2 w-2 rounded-full' : 'inline-block h-2 w-2.5 rounded-[2px]'}
        style={{ background: color }}
      />
      {label}
    </span>
  )
}
