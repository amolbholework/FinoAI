import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatMoney } from '../lib/format'
import { Skeleton } from '../components/Skeleton'
import { WhatIfSpotArt } from '../components/illustrations/WhatIfSpotArt'
import { EmptyTransactionsArt } from '../components/illustrations/EmptyTransactionsArt'
import type { Goal, SavingsRate } from '../lib/types'

const CHART_WIDTH = 700
const CHART_HEIGHT = 240
const MONTHS_AHEAD = 6
const MAX_ADJUSTABLE_CATEGORIES = 6

interface CategorySpend {
  name: string
  monthlyMinor: number
}

// Ported faithfully from the original design reference's buildPath(): maps a
// constant monthly savings rate forward from today's saved amount into an
// SVG path, auto-scaling the y-axis to whatever range the two scenarios need.
function buildPath(monthlySavingsMinor: number, savedNowMinor: number): string {
  const points: number[] = []
  for (let m = 0; m <= MONTHS_AHEAD; m++) points.push(savedNowMinor + monthlySavingsMinor * m)

  const min = Math.min(...points, 0)
  const max = Math.max(...points, 100_000_00)
  const range = max - min || 1
  const toY = (v: number) => CHART_HEIGHT - 30 - ((v - min) / range) * (CHART_HEIGHT - 50)
  const toX = (i: number) => (i / MONTHS_AHEAD) * CHART_WIDTH

  return points.map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ')
}

function fmtSigned(minor: number, currency: string): string {
  const sign = minor < 0 ? '-' : minor > 0 ? '+' : ''
  return minor === 0 ? formatMoney(0, currency) : `${sign}${formatMoney(Math.abs(minor), currency)}`
}

export function WhatIfPage() {
  const currency = useCurrency()
  const [adjustPct, setAdjustPct] = useState<Record<string, number>>({})
  const [incomeChangeMinor, setIncomeChangeMinor] = useState(0)
  const [oneOffMinor, setOneOffMinor] = useState(0)

  const [categories, setCategories] = useState<CategorySpend[] | null>(null)
  const [totalSpendMinor, setTotalSpendMinor] = useState<number | null>(null)
  const [monthlyIncomeMinor, setMonthlyIncomeMinor] = useState<number | null>(null)
  const [goal, setGoal] = useState<Goal | null | undefined>(undefined)
  const [error, setError] = useState(false)
  const [loadToken, setLoadToken] = useState(0)

  useEffect(() => {
    let cancelled = false
    setError(false)

    Promise.all([api.get<SavingsRate[]>('/analysis/savings-rate'), api.get<Goal[]>('/goals')])
      .then(async ([savingsRes, goalsRes]) => {
        if (cancelled) return
        const latest = savingsRes.data[savingsRes.data.length - 1] ?? null

        setMonthlyIncomeMinor(latest?.income_minor ?? 0)
        setTotalSpendMinor(latest?.spend_minor ?? 0)
        // The nearest-target-date goal, same ordering the Goals page uses.
        // Its own saved_amount_minor — not the account's overall balance —
        // is what "current saved" means here: progress toward this one
        // goal, not everything in the account.
        setGoal(goalsRes.data[0] ?? null)

        if (!latest) {
          setCategories([])
          return
        }
        const breakdownRes = await api.get<Record<string, number>>('/analysis/category-breakdown', {
          params: { month: latest.month },
        })
        if (cancelled) return
        const entries = Object.entries(breakdownRes.data)
          .sort(([, a], [, b]) => b - a)
          .slice(0, MAX_ADJUSTABLE_CATEGORIES)
          .map(([name, monthlyMinor]) => ({ name, monthlyMinor }))
        setCategories(entries)
      })
      .catch(() => !cancelled && setError(true))

    return () => {
      cancelled = true
    }
  }, [loadToken])

  const totalCategoriesShownMinor = useMemo(() => categories?.reduce((s, c) => s + c.monthlyMinor, 0) ?? 0, [categories])
  // Spend outside the top shown categories — folded into the baseline as a
  // non-adjustable remainder rather than dropped, so totals stay honest.
  const otherSpendMinor = Math.max((totalSpendMinor ?? 0) - totalCategoriesShownMinor, 0)

  const baselineSpendMinor = totalCategoriesShownMinor + otherSpendMinor
  const baselineSavingsMinor = (monthlyIncomeMinor ?? 0) - baselineSpendMinor

  const simulatedSpendMinor = useMemo(() => {
    const variable = (categories ?? []).reduce((sum, c) => {
      const pct = adjustPct[c.name] ?? 0
      return sum + c.monthlyMinor * (1 + pct / 100)
    }, 0)
    return Math.round(variable) + otherSpendMinor
  }, [categories, adjustPct, otherSpendMinor])

  const simulatedIncomeMinor = (monthlyIncomeMinor ?? 0) + incomeChangeMinor
  const simulatedSavingsMinor = simulatedIncomeMinor - simulatedSpendMinor

  const savedNowMinor = goal?.saved_amount_minor ?? 0
  const remainingGoalMinor = goal ? Math.max(goal.target_amount_minor - savedNowMinor + oneOffMinor, 0) : null
  const monthsBaseline =
    goal && baselineSavingsMinor > 0 ? (goal.target_amount_minor - savedNowMinor) / baselineSavingsMinor : null
  const monthsSimulated =
    goal && remainingGoalMinor !== null && simulatedSavingsMinor > 0 ? remainingGoalMinor / simulatedSavingsMinor : null

  const baselinePath = buildPath(baselineSavingsMinor, savedNowMinor)
  const simulatedPath = buildPath(simulatedSavingsMinor, savedNowMinor - oneOffMinor)

  const deltaMinor = simulatedSavingsMinor - baselineSavingsMinor
  const monthsToGoalDelta = monthsBaseline !== null && monthsSimulated !== null ? monthsBaseline - monthsSimulated : null

  function reset() {
    setAdjustPct({})
    setIncomeChangeMinor(0)
    setOneOffMinor(0)
  }

  if (error) {
    return (
      <div className="card-lifted flex flex-col items-center gap-3 px-6 py-16 text-center">
        <h2 className="font-heading text-lg font-semibold text-heading">Couldn't load the what-if simulator</h2>
        <p className="max-w-sm text-sm text-secondary">Something went wrong fetching your data.</p>
        <button onClick={() => setLoadToken((t) => t + 1)} className="mt-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">
          Try again
        </button>
      </div>
    )
  }

  if (categories === null || monthlyIncomeMinor === null || goal === undefined) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    )
  }

  if (categories.length === 0) {
    return (
      <div className="card-lifted flex flex-col items-center gap-3 px-6 py-16 text-center">
        <EmptyTransactionsArt />
        <h2 className="font-heading text-lg font-semibold text-heading">Not enough data yet</h2>
        <p className="max-w-sm text-sm text-secondary">
          Add some transactions to see your spending broken down here — then you can model what changing it would do.
        </p>
        <Link to="/import" className="mt-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">
          Add transactions
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 flex items-baseline justify-between">
        <div className="flex items-center gap-3">
          <WhatIfSpotArt />
          <div>
            <h1 className="font-heading text-h2 font-bold text-heading">What-if simulator</h1>
            <p className="mt-1.5 text-sm text-muted">Adjust the levers and watch your forecast move</p>
          </div>
        </div>
        <button onClick={reset} className="rounded-sm bg-hairline px-4.5 py-2.5 text-[13.5px] font-semibold text-secondary">
          Reset
        </button>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[340px_1fr]">
        {/* CONTROLS */}
        <div className="card-lifted p-7">
          <div className="font-heading mb-5 text-[15px] font-semibold text-heading">Adjust categories</div>
          <div className="mb-7 flex flex-col gap-5.5">
            {categories.map((cat) => {
              const pct = adjustPct[cat.name] ?? 0
              const deltaCatMinor = cat.monthlyMinor * (pct / 100)
              return (
                <div key={cat.name}>
                  <div className="mb-2 flex justify-between text-[13.5px]">
                    <span className="font-medium text-body">{cat.name}</span>
                    <span className="tabular-nums text-muted">{formatMoney(cat.monthlyMinor, currency)}/mo</span>
                  </div>
                  <input
                    type="range"
                    min={-50}
                    max={50}
                    step={5}
                    value={pct}
                    onChange={(e) => setAdjustPct((a) => ({ ...a, [cat.name]: Number(e.target.value) }))}
                    className="w-full accent-primary"
                  />
                  <div className="mt-1 text-right text-xs tabular-nums" style={{ color: pct === 0 ? 'var(--color-muted)' : pct > 0 ? 'var(--color-overspend)' : 'var(--color-positive)' }}>
                    {fmtSigned(deltaCatMinor, currency)}/mo
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex flex-col gap-5.5 border-t border-hairline pt-5.5">
            <div>
              <div className="mb-2 flex justify-between text-[13.5px]">
                <span className="font-medium text-body">Income change</span>
                <span
                  className="tabular-nums font-semibold"
                  style={{ color: incomeChangeMinor === 0 ? 'var(--color-muted)' : incomeChangeMinor > 0 ? 'var(--color-positive)' : 'var(--color-overspend)' }}
                >
                  {fmtSigned(incomeChangeMinor, currency)}/mo
                </span>
              </div>
              <input
                type="range"
                min={-10000_00}
                max={10000_00}
                step={500_00}
                value={incomeChangeMinor}
                onChange={(e) => setIncomeChangeMinor(Number(e.target.value))}
                className="w-full accent-positive"
              />
            </div>
            <div>
              <label className="mb-2 block text-[13.5px] font-medium text-body">One-off large purchase</label>
              <div className="flex items-center rounded-md border-[1.5px] border-border bg-canvas px-3.5 py-2.5">
                <span className="mr-1 text-[15px] text-muted">₹</span>
                <input
                  type="number"
                  min={0}
                  step={1000}
                  value={oneOffMinor / 100}
                  onChange={(e) => setOneOffMinor(Math.round(Number(e.target.value || 0) * 100))}
                  className="w-full bg-transparent text-[15px] text-body outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* CHART + SUMMARY */}
        <div>
          <div className="card-lifted mb-5 p-8">
            <div className="mb-5.5 flex items-baseline justify-between">
              <div className="font-heading text-[17px] font-semibold text-heading">Savings trajectory, next 6 months</div>
              <div className="flex gap-4">
                <span className="flex items-center gap-1.5 text-xs text-muted">
                  <span className="inline-block h-0.5 w-3.5" style={{ background: 'var(--color-border)' }} />
                  Baseline
                </span>
                <span className="flex items-center gap-1.5 text-xs text-muted">
                  <span className="inline-block h-0.5 w-3.5" style={{ background: 'var(--color-primary)' }} />
                  Simulated
                </span>
              </div>
            </div>
            <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} width="100%" height="240" style={{ overflow: 'visible' }}>
              <line x1="0" y1="20" x2={CHART_WIDTH} y2="20" stroke="var(--color-hairline)" strokeWidth="1" />
              <line x1="0" y1="80" x2={CHART_WIDTH} y2="80" stroke="var(--color-hairline)" strokeWidth="1" />
              <line x1="0" y1="140" x2={CHART_WIDTH} y2="140" stroke="var(--color-hairline)" strokeWidth="1" />
              <line x1="0" y1="200" x2={CHART_WIDTH} y2="200" stroke="var(--color-hairline)" strokeWidth="1" />
              <path d={baselinePath} fill="none" stroke="var(--color-border)" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="1,7" />
              <path d={simulatedPath} fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <div className="mt-2 flex justify-between px-1 text-xs text-muted">
              <span>Now</span>
              <span>+1mo</span>
              <span>+2mo</span>
              <span>+3mo</span>
              <span>+4mo</span>
              <span>+5mo</span>
              <span>+6mo</span>
            </div>
          </div>

          <div className="card-lifted grid grid-cols-1 gap-6 p-7 sm:grid-cols-3">
            <div>
              <div className="mb-2 text-[12.5px] text-muted">Monthly savings</div>
              <div className="font-heading text-h4 font-bold tabular-nums text-heading">
                {formatMoney(simulatedSavingsMinor, currency)}
              </div>
            </div>
            <div>
              <div className="mb-2 text-[12.5px] text-muted">Savings delta vs. baseline</div>
              <div
                className="font-heading text-h4 font-bold tabular-nums"
                style={{ color: deltaMinor === 0 ? 'var(--color-heading)' : deltaMinor > 0 ? 'var(--color-positive)' : 'var(--color-overspend)' }}
              >
                {fmtSigned(deltaMinor, currency)}
              </div>
            </div>
            <div>
              {goal ? (
                <>
                  <div className="mb-2 text-[12.5px] text-muted">Months to "{goal.name}"</div>
                  <div className="font-heading text-h4 font-bold tabular-nums text-heading">
                    {monthsSimulated === null ? 'Not on pace' : `${monthsSimulated.toFixed(1)} mo`}
                  </div>
                  {monthsToGoalDelta !== null && (
                    <div className="mt-0.5 text-xs" style={{ color: monthsToGoalDelta >= 0 ? 'var(--color-positive)' : 'var(--color-overspend)' }}>
                      {monthsToGoalDelta >= 0 ? `${monthsToGoalDelta.toFixed(1)} mo sooner` : `${Math.abs(monthsToGoalDelta).toFixed(1)} mo later`}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="mb-2 text-[12.5px] text-muted">Months to goal</div>
                  <Link to="/goals" className="text-sm font-semibold text-primary hover:underline">
                    Set a goal →
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
