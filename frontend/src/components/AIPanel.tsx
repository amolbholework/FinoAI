import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../lib/api'
import { Skeleton } from './Skeleton'
import type { Recommendations } from '../lib/types'

const PRIORITY_STYLE: Record<string, string> = {
  high: 'bg-[var(--color-overspend-soft)] text-[var(--color-overspend-ink)]',
  medium: 'bg-[var(--color-warning-soft)] text-[var(--color-warning-ink)]',
  low: 'bg-[var(--color-positive-soft)] text-[var(--color-positive-ink)]',
}

export function AIPanel({
  data,
  isLoading,
  onRefresh,
}: {
  data: Recommendations | null
  isLoading: boolean
  onRefresh: () => void
}) {
  const [refreshing, setRefreshing] = useState(false)

  async function handleRefresh() {
    setRefreshing(true)
    try {
      await onRefresh()
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div
      className="rounded-2xl p-6"
      style={{
        background: 'linear-gradient(135deg, var(--color-ai-soft), var(--color-card))',
        boxShadow: 'var(--shadow-card)',
        border: '1px solid var(--color-primary-border)',
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white">
            AI
          </span>
          <h2 className="font-heading text-base font-semibold text-heading">FinPilot Advisor</h2>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || isLoading}
          className="text-xs font-medium text-primary hover:underline disabled:opacity-50"
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {isLoading ? (
        <div className="mt-4 space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ) : data ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mt-4 space-y-4"
        >
          <p className="text-sm leading-relaxed text-heading">{data.summary}</p>

          {data.insights.length > 0 && (
            <ul className="space-y-1.5">
              {data.insights.map((insight, i) => (
                <li key={i} className="flex gap-2 text-sm text-secondary">
                  <span className="text-primary">•</span>
                  {insight}
                </li>
              ))}
            </ul>
          )}

          {data.recommendations.length > 0 && (
            <div className="space-y-2">
              {data.recommendations.map((rec, i) => (
                <div key={i} className="rounded-xl border border-border bg-card/70 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-heading">{rec.title}</p>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${PRIORITY_STYLE[rec.priority]}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-secondary">{rec.rationale}</p>
                  <p className="money mt-1 text-xs font-medium text-primary">{rec.projected_impact}</p>
                </div>
              ))}
            </div>
          )}

          {data.risks.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">Risks</p>
              <ul className="mt-1 space-y-1">
                {data.risks.map((risk, i) => (
                  <li key={i} className="text-xs text-[var(--color-overspend)]">
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.cached && <p className="text-[10px] text-muted">Cached — data hasn't changed since last generation.</p>}
        </motion.div>
      ) : null}
    </div>
  )
}

export async function fetchRecommendations(forceRefresh = false): Promise<Recommendations> {
  const res = await api.get('/ai/recommendations', { params: { force_refresh: forceRefresh } })
  return res.data
}
