import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatDate, formatMoney } from '../lib/format'
import { useFino } from '../context/FinoContext'
import { Skeleton } from '../components/Skeleton'
import { AdviceRecommendationCard } from '../components/AdviceRecommendationCard'
import { EmptyAdviceArt } from '../components/illustrations/EmptyAdviceArt'
import type { AdviceHistoryItem, AdviceHorizon, AdviceRecommendation, AdviceResponse, Category, RecommendationStatus } from '../lib/types'

const SEVERITY_STYLE: Record<string, { border: string; text: string }> = {
  urgent: { border: 'var(--color-overspend)', text: 'var(--color-overspend-ink)' },
  watch: { border: 'var(--color-warning)', text: 'var(--color-warning-ink)' },
  info: { border: 'var(--color-border)', text: 'var(--color-secondary)' },
}

const EFFORT_WEIGHT: Record<string, number> = { low: 1, medium: 2, high: 3 }

const HORIZON_GROUPS: { key: AdviceHorizon; label: string }[] = [
  { key: 'this_month', label: 'This month' },
  { key: 'next_3_months', label: 'Next 3 months' },
  { key: 'long_term', label: 'Long term' },
]

function priorityScore(r: AdviceRecommendation): number {
  return r.impact_inr_per_month / (EFFORT_WEIGHT[r.effort] ?? 2)
}

export function AdvicePage() {
  const currency = useCurrency()
  const navigate = useNavigate()
  const { openPanel, sendMessage } = useFino()
  const [data, setData] = useState<AdviceResponse | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [history, setHistory] = useState<AdviceHistoryItem[]>([])
  const [error, setError] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    api.get<Category[]>('/categories').then((res) => setCategories(res.data))
    loadHistory()
    load(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function load(forceRefresh: boolean) {
    setError(false)
    try {
      const res = await api.post<AdviceResponse>('/api/advice', null, { params: { force_refresh: forceRefresh } })
      setData(res.data)
      if (!res.data.cached) loadHistory()
    } catch {
      setError(true)
    }
  }

  function loadHistory() {
    api.get<AdviceHistoryItem[]>('/api/advice/history').then((res) => setHistory(res.data)).catch(() => {})
  }

  async function handleRefresh() {
    setRefreshing(true)
    try {
      await load(true)
    } finally {
      setRefreshing(false)
    }
  }

  async function handleStatusChange(id: string, status: RecommendationStatus) {
    if (!data) return
    // Optimistic update — the advice row is cached server-side, so this PATCH
    // persists against that same row regardless of when it's next fetched.
    setData({ ...data, recommendations: data.recommendations.map((r) => (r.id === id ? { ...r, status } : r)) })
    try {
      await api.patch(`/api/advice/recommendations/${id}/status`, { status })
    } catch {
      // Leave the optimistic state — a failed PATCH here isn't worth interrupting the user for.
    }
  }

  function handleAskFino(rec: AdviceRecommendation) {
    openPanel()
    sendMessage(`Why do you recommend this? "${rec.action}" — ${rec.why}`)
  }

  const evidenceLink = useMemo(() => {
    return (metric: string, period: string) => {
      const match = categories.find((c) => metric.toLowerCase().includes(c.name.toLowerCase()))
      if (!match) return null
      const periodMatch = /^(\d{4})-(\d{2})$/.exec(period)
      const params = new URLSearchParams({ category_id: match.id })
      if (periodMatch) {
        const [, year, month] = periodMatch
        const lastDay = new Date(Number(year), Number(month), 0).getDate()
        params.set('date_from', `${year}-${month}-01`)
        params.set('date_to', `${year}-${month}-${String(lastDay).padStart(2, '0')}`)
      }
      return `/transactions?${params.toString()}`
    }
  }, [categories])

  const topPriorityId = useMemo(() => {
    const pending = (data?.recommendations ?? []).filter((r) => r.status === 'pending')
    if (pending.length === 0) return null
    return pending.reduce((best, r) => (priorityScore(r) > priorityScore(best) ? r : best)).id
  }, [data])

  const topPriorityRec = data?.recommendations.find((r) => r.id === topPriorityId) ?? null

  const groupedRecommendations = useMemo(() => {
    const recs = data?.recommendations ?? []
    return HORIZON_GROUPS.map((group) => ({
      ...group,
      items: recs.filter((r) => r.horizon === group.key).sort((a, b) => priorityScore(b) - priorityScore(a)),
    })).filter((group) => group.items.length > 0)
  }, [data])

  if (error) {
    return (
      <div className="card-lifted px-6 py-16 text-center">
        <p className="text-sm text-muted">Couldn't load your advice right now.</p>
        <button onClick={() => load(false)} className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">
          Try again
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-48 w-full rounded-2xl" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-h2 font-bold text-heading">AI Advisor</h1>
          <p className="mt-1.5 text-sm text-muted">Recommendations grounded in your actual numbers — advisory only, see disclaimer below.</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-secondary hover:bg-hairline disabled:opacity-50"
        >
          {refreshing ? 'Refreshing…' : 'Refresh advice'}
        </button>
      </div>

      {data.is_fallback && (
        <div className="mb-6 rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] px-4 py-3 text-sm text-[var(--color-warning-ink)]">
          AI advice is temporarily unavailable — showing a rule-based summary from your numbers instead. Try refreshing in a moment.
        </div>
      )}

      <div className="mb-8 rounded-2xl p-6" style={{ background: 'linear-gradient(135deg, var(--color-ai-soft), var(--color-card))', border: '1px solid var(--color-primary-border)' }}>
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold text-white" style={{ background: 'var(--color-ai)' }}>
            AI
          </span>
          <span className="text-xs font-semibold uppercase tracking-wide text-muted">FinPilot Advisor{data.cached ? ' · cached' : ''}</span>
        </div>
        <p className="mt-3 text-base font-medium leading-relaxed text-heading">{data.headline}</p>
      </div>

      {data.insights.length > 0 && (
        <div className="mb-8">
          <h2 className="font-heading mb-4 text-base font-semibold text-heading">Insights</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {data.insights.map((insight, i) => {
              const style = SEVERITY_STYLE[insight.severity] ?? SEVERITY_STYLE.info
              const link = evidenceLink(insight.evidence.metric, insight.evidence.period)
              return (
                <div key={i} className="rounded-xl border p-4" style={{ borderColor: `${style.border}55` }}>
                  <p className="text-sm font-semibold text-heading">{insight.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-secondary">{insight.detail}</p>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span style={{ color: style.text }}>
                      {insight.evidence.metric}: {insight.evidence.value} ({insight.evidence.period})
                    </span>
                    {link && (
                      <button onClick={() => navigate(link)} className="font-medium text-primary hover:underline">
                        View transactions →
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="mb-8">
        <h2 className="font-heading mb-1 text-base font-semibold text-heading">Recommendations</h2>
        {topPriorityRec && (
          <p className="mb-4 text-xs text-muted">
            <span className="font-medium text-primary">"{topPriorityRec.action}"</span> is prioritized first — the highest estimated impact
            ({formatMoney(Math.round(topPriorityRec.impact_inr_per_month * 100), currency)}/mo) for its effort level, of everything not yet
            acted on.
          </p>
        )}
        {data.recommendations.length === 0 ? (
          <div className="card flex flex-col items-center gap-2 p-6 text-center">
            <EmptyAdviceArt />
            <p className="text-sm text-muted">Not enough data yet for specific recommendations — add more transactions to unlock these.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {groupedRecommendations.map((group) => (
              <div key={group.key}>
                <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-muted">{group.label}</h3>
                <div className="flex flex-col gap-3">
                  {group.items.map((rec) => (
                    <AdviceRecommendationCard
                      key={rec.id}
                      recommendation={rec}
                      currency={currency}
                      onStatusChange={handleStatusChange}
                      onAskFino={handleAskFino}
                      isTopPriority={rec.id === topPriorityId}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {data.questions_to_consider.length > 0 && (
        <div className="mb-8 card p-6">
          <h2 className="font-heading mb-3 text-base font-semibold text-heading">Questions worth thinking about</h2>
          <ul className="space-y-1.5">
            {data.questions_to_consider.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-secondary">
                <span className="text-primary">•</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      {history.length > 1 && (
        <div className="card p-6">
          <h2 className="font-heading mb-3 text-base font-semibold text-heading">History</h2>
          <ul className="space-y-2.5">
            {history.map((h) => (
              <li key={h.advice_id} className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 flex-1 truncate text-secondary">
                  {h.headline}
                  {h.is_fallback && <span className="ml-1.5 text-[10px] uppercase text-muted">(fallback)</span>}
                </span>
                <span className="flex-none text-xs text-muted">
                  {formatDate(h.generated_at.slice(0, 10))} · score {h.health_score}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
