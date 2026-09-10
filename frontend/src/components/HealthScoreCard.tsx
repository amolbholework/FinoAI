import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { HealthScoreResponse } from '../lib/types'

const DISMISSED_KEY = 'fp-health-card-dismissed'

const BAND_COLOR: Record<string, string> = {
  'Needs attention': 'var(--color-muted)',
  'Getting there': 'var(--color-warning)',
  Stable: 'var(--color-positive)',
  Strong: 'var(--color-primary)',
}

/** Dashboard entry point for the (optional, feature-flagged) Health
 * Checker. Fails silently — a 404 (flag off) or any other error just
 * means the card doesn't render, same as having no data. Dismissal
 * persists locally so it doesn't reappear every visit once closed. */
export function HealthScoreCard() {
  const [data, setData] = useState<HealthScoreResponse | null>(null)
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISSED_KEY) === '1')

  useEffect(() => {
    if (dismissed) return
    api
      .get<HealthScoreResponse>('/api/health/score')
      .then((res) => setData(res.data))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function dismiss() {
    localStorage.setItem(DISMISSED_KEY, '1')
    setDismissed(true)
  }

  if (dismissed || !data || data.score === null) return null

  return (
    <div className="card-lifted flex items-center gap-4 p-5">
      <div
        className="flex h-14 w-14 flex-none items-center justify-center rounded-full text-lg font-bold tabular-nums text-white"
        style={{ background: BAND_COLOR[data.band ?? ''] ?? 'var(--color-muted)' }}
      >
        {data.score}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-heading">
          Financial health: <span style={{ color: BAND_COLOR[data.band ?? ''] ?? 'var(--color-muted)' }}>{data.band}</span>
        </p>
        <p className="mt-0.5 text-xs text-secondary">A deterministic score from your own data — see the full breakdown.</p>
      </div>
      <Link to="/health" className="flex-none rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-white">
        View
      </Link>
      <button onClick={dismiss} aria-label="Dismiss" className="flex-none text-muted hover:text-heading">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}
