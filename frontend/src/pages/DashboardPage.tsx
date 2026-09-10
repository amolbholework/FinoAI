import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { useCurrency } from '../lib/currency'
import { formatDate, formatMoney, formatMonth } from '../lib/format'
import { StatTile } from '../components/StatTile'
import { TrendChart } from '../components/TrendChart'
import { CategoryBreakdown } from '../components/CategoryBreakdown'
import { ChartCaption } from '../components/ChartCaption'
import { BurnRateStrip } from '../components/BurnRateStrip'
import { AnomalyCard } from '../components/AnomalyCard'
import { QuickActions } from '../components/QuickActions'
import { HealthScoreCard } from '../components/HealthScoreCard'
import { DashboardEmptyState } from '../components/DashboardEmptyState'
import { DashboardErrorState } from '../components/DashboardErrorState'
import { MarketIndicesSection } from '../components/MarketIndicesSection'
import { AIPanel, fetchRecommendations } from '../components/AIPanel'
import type {
  BudgetAdherence,
  Category,
  CategoryMonthAnomaly,
  DashboardSummary,
  Forecast,
  Recommendations,
  TransactionAnomaly,
} from '../lib/types'

const GOAL_LABELS: Record<string, string> = {
  emergency_fund: 'building an emergency fund',
  debt_payoff: 'paying off debt',
  home_purchase: 'buying a home',
  education: 'education',
  retirement: 'retirement',
  travel: 'travel or a big purchase',
  wealth_building: 'general wealth building',
}

const REVEAL_CONTAINER = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}

const REVEAL_ITEM = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as const } },
}

export function DashboardPage() {
  const currency = useCurrency()
  const navigate = useNavigate()
  const reduceMotion = useReducedMotion()
  const { profile } = useAuth()

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [summaryError, setSummaryError] = useState(false)
  const [monthlyTotals, setMonthlyTotals] = useState<Record<string, number> | null>(null)
  const [categoryBreakdown, setCategoryBreakdown] = useState<Record<string, number> | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [adherence, setAdherence] = useState<BudgetAdherence[] | null>(null)
  const [txnAnomalies, setTxnAnomalies] = useState<TransactionAnomaly[]>([])
  const [categoryAnomalies, setCategoryAnomalies] = useState<CategoryMonthAnomaly[]>([])
  const [recommendations, setRecommendations] = useState<Recommendations | null>(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [loadToken, setLoadToken] = useState(0)

  useEffect(() => {
    let cancelled = false
    setSummaryError(false)

    api
      .get<DashboardSummary>('/analysis/dashboard-summary')
      .then((res) => !cancelled && setSummary(res.data))
      .catch(() => !cancelled && setSummaryError(true))

    api.get('/analysis/monthly-totals').then((res) => !cancelled && setMonthlyTotals(res.data))
    api.get<Category[]>('/categories').then((res) => !cancelled && setCategories(res.data))
    api.get('/forecasts/latest').then((res) => !cancelled && setForecast(res.data))
    api.get('/analysis/budget-adherence').then((res) => !cancelled && setAdherence(res.data))
    api.get('/analysis/anomalies').then((res) => {
      if (cancelled) return
      setTxnAnomalies(res.data.transactions ?? [])
      setCategoryAnomalies(res.data.category_months ?? [])
    })
    fetchRecommendations()
      .then((data) => !cancelled && setRecommendations(data))
      .finally(() => !cancelled && setAiLoading(false))

    return () => {
      cancelled = true
    }
  }, [loadToken])

  const months = monthlyTotals ? Object.keys(monthlyTotals).sort() : []
  const latestMonth = months[months.length - 1]

  // Category breakdown depends on knowing the latest month first, so it's
  // fetched once monthlyTotals resolves rather than in the initial batch.
  useEffect(() => {
    if (!latestMonth) return
    api.get('/analysis/category-breakdown', { params: { month: latestMonth } }).then((res) => setCategoryBreakdown(res.data))
  }, [latestMonth])

  const overBudget = adherence?.filter((b) => b.is_over) ?? []

  async function handleAiRefresh() {
    setAiLoading(true)
    try {
      const data = await fetchRecommendations(true)
      setRecommendations(data)
    } finally {
      setAiLoading(false)
    }
  }

  function goToCategory(category: string) {
    const match = categories.find((c) => c.name === category)
    navigate(match ? `/transactions?category_id=${match.id}` : '/transactions')
  }

  const daysInMonth = useMemo(() => {
    if (!summary) return 30
    const [year, month] = summary.spend_to_date.current_month.split('-').map(Number)
    return new Date(year, month, 0).getDate()
  }, [summary])

  const budgetLimitMinor =
    summary && summary.remaining_budget.total_limit_minor > 0 ? summary.remaining_budget.total_limit_minor : null

  const spendCaption = useMemo(() => {
    if (!summary) return null
    const { spend_to_date_minor, days_elapsed, pct_change, current_month } = summary.spend_to_date
    const monthLabel = formatMonth(current_month)
    const spendText = formatMoney(spend_to_date_minor, currency)
    if (pct_change === null) {
      return `You've spent ${spendText} in the first ${days_elapsed} days of ${monthLabel}.`
    }
    const direction = pct_change >= 0 ? 'more' : 'less'
    return `You've spent ${spendText} in the first ${days_elapsed} days of ${monthLabel} — ${Math.abs(pct_change).toFixed(0)}% ${direction} than the same point last month.`
  }, [summary, currency])

  const paceCaption = useMemo(() => {
    if (!summary) return null
    const projected = formatMoney(summary.projected_month_end_spend_minor, currency)
    if (budgetLimitMinor != null) {
      const overBy = summary.projected_month_end_spend_minor - budgetLimitMinor
      if (overBy > 0) {
        return `At this pace you're on track to go ${formatMoney(overBy, currency)} over your ${formatMoney(budgetLimitMinor, currency)} budget by month end.`
      }
      return `At this pace you're on track to land ${formatMoney(-overBy, currency)} under your ${formatMoney(budgetLimitMinor, currency)} budget.`
    }
    return `At this pace you're on track to spend about ${projected} by the end of the month. Set a budget to get an on-track vs. over-budget read.`
  }, [summary, currency, budgetLimitMinor])

  const topCategoryCaption = useMemo(() => {
    if (!summary || summary.top_categories.length === 0) return null
    const top = summary.top_categories[0]
    return `${top.category} is your biggest expense so far this month, at ${top.pct_of_total.toFixed(0)}% of total spend.`
  }, [summary])

  const combinedAnomalies = useMemo(() => {
    const fromTxns = txnAnomalies.map((a) => ({
      key: `txn-${a.date}-${a.category}`,
      title: `Unusual ${a.category} transaction`,
      description: `on ${formatDate(a.date)}`,
      amountMinor: a.amount_minor,
      zScore: a.z_score,
    }))
    const fromCategories = categoryAnomalies.map((a) => ({
      key: `cat-${a.month}-${a.category}`,
      title: `${a.category} spent more than usual`,
      description: `in ${formatMonth(a.month)}`,
      amountMinor: -a.spend_minor,
      zScore: a.z_score,
    }))
    return [...fromTxns, ...fromCategories].sort((a, b) => b.zScore - a.zScore).slice(0, 4)
  }, [txnAnomalies, categoryAnomalies])

  const hasNoData = monthlyTotals !== null && Object.keys(monthlyTotals).length === 0

  if (summaryError) {
    return <DashboardErrorState onRetry={() => setLoadToken((t) => t + 1)} />
  }

  const Container = reduceMotion ? 'div' : motion.div
  const Item = reduceMotion ? 'div' : motion.div
  const containerProps = reduceMotion ? {} : { variants: REVEAL_CONTAINER, initial: 'hidden', animate: 'show' }
  const itemProps = reduceMotion ? {} : { variants: REVEAL_ITEM }

  // A single onboarding-derived nudge — literacy takes priority over goals
  // since "learn the basics" is the more foundational next step. Null when
  // there's no profile signal to act on (skipped onboarding, or a profile
  // that matches neither condition) — purely additive.
  const personalizedNudge = !profile
    ? null
    : profile.literacy_level === 'beginner'
      ? { text: 'New to investing? Start with the Money Basics module.', to: '/learn', cta: 'Start learning' }
      : profile.goals[0]
        ? {
            text: `You told us ${GOAL_LABELS[profile.goals[0].type] ?? profile.goals[0].type} matters to you — set a target on the Goals page to start tracking it.`,
            to: '/goals',
            cta: 'Set a goal',
          }
        : null

  return (
    <Container className="space-y-8" {...containerProps}>
      <Item {...itemProps}>
        <QuickActions />
      </Item>

      <Item {...itemProps}>
        <HealthScoreCard />
      </Item>

      {personalizedNudge && (
        <Item
          {...itemProps}
          className="flex items-center justify-between gap-4 rounded-xl border border-primary-border bg-primary-soft px-4 py-3 text-sm"
        >
          <span className="text-heading">{personalizedNudge.text}</span>
          <Link to={personalizedNudge.to} className="flex-none font-semibold text-primary hover:underline">
            {personalizedNudge.cta} →
          </Link>
        </Item>
      )}

      {hasNoData ? (
        <Item {...itemProps}>
          <DashboardEmptyState />
        </Item>
      ) : (
        <>
          <Item {...itemProps} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatTile
              label="Spent so far this month"
              value={summary?.spend_to_date.spend_to_date_minor ?? null}
              formatter={(n) => formatMoney(n, currency)}
              tone="accent"
              delta={
                summary && summary.spend_to_date.pct_change !== null
                  ? { pct: summary.spend_to_date.pct_change, label: 'vs same point last month' }
                  : null
              }
            />
            <StatTile
              label="Projected month-end spend"
              value={summary?.projected_month_end_spend_minor ?? null}
              formatter={(n) => formatMoney(n, currency)}
            />
            <StatTile
              label={budgetLimitMinor != null ? 'Remaining budget' : 'Next month forecast'}
              value={budgetLimitMinor != null ? (summary?.remaining_budget.remaining_minor ?? null) : (forecast?.predicted_total_minor ?? null)}
              formatter={(n) => formatMoney(n, currency)}
            />
          </Item>

          <Item {...itemProps} className="card-lifted p-6">
            <h2 className="font-heading text-base font-semibold text-heading">Burn rate this month</h2>
            <div className="mt-4">
              <BurnRateStrip dailyBurn={summary?.daily_burn ?? null} daysInMonth={daysInMonth} budgetLimitMinor={budgetLimitMinor} currency={currency} />
            </div>
            <ChartCaption>
              {spendCaption} {paceCaption}
            </ChartCaption>
          </Item>

          {overBudget.length > 0 && (
            <Item
              {...itemProps}
              className="rounded-xl border border-[var(--color-overspend)]/20 bg-[var(--color-overspend-soft)] px-4 py-3 text-sm text-[var(--color-overspend-ink)]"
            >
              Over budget in {overBudget.map((b) => b.category).join(', ')} this month.
            </Item>
          )}

          <Item {...itemProps}>
            <AIPanel data={recommendations} isLoading={aiLoading} onRefresh={handleAiRefresh} />
          </Item>

          {combinedAnomalies.length > 0 && (
            <Item {...itemProps}>
              <h2 className="font-heading mb-3 text-base font-semibold text-heading">Worth a look</h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {combinedAnomalies.map((a) => (
                  <AnomalyCard
                    key={a.key}
                    title={a.title}
                    description={a.description}
                    amountMinor={a.amountMinor}
                    currency={currency}
                    severity={a.zScore >= 3 ? 'high' : 'medium'}
                  />
                ))}
              </div>
            </Item>
          )}

          <Item {...itemProps} className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="card-lifted p-6 lg:col-span-2">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-heading text-base font-semibold text-heading">Spending trend</h2>
                {forecast?.is_low_confidence && (
                  <span className="rounded-full bg-[var(--color-warning-soft)] px-2 py-0.5 text-[10px] font-semibold uppercase text-[var(--color-warning-ink)]">
                    Low-confidence forecast
                  </span>
                )}
              </div>
              <TrendChart monthlyTotals={monthlyTotals} forecast={forecast} currency={currency} />
              <ChartCaption>Monthly total spend, with next month's forecast range shaded at the right.</ChartCaption>
            </div>

            <div className="card-lifted p-6">
              <h2 className="font-heading mb-4 text-base font-semibold text-heading">By category</h2>
              <CategoryBreakdown data={categoryBreakdown} currency={currency} onCategoryClick={goToCategory} />
              <ChartCaption>{topCategoryCaption ?? 'Tap a category to see its transactions.'}</ChartCaption>
            </div>
          </Item>

          <Item {...itemProps}>
            <MarketIndicesSection />
          </Item>
        </>
      )}
    </Container>
  )
}
