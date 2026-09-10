import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { formatMonth } from '../lib/format'
import { HealthGauge } from '../components/HealthGauge'
import { Skeleton } from '../components/Skeleton'
import { EmptyHealthDataArt } from '../components/illustrations/EmptyHealthDataArt'
import type { HealthScoreResponse } from '../lib/types'

const BAND_COLOR: Record<string, string> = {
  'Needs attention': 'var(--color-muted)',
  'Getting there': 'var(--color-warning)',
  Stable: 'var(--color-positive)',
  Strong: 'var(--color-primary)',
}

export function HealthCheckerPage() {
  const [data, setData] = useState<HealthScoreResponse | null>(null)
  const [error, setError] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explaining, setExplaining] = useState(false)

  useEffect(() => {
    api
      .get<HealthScoreResponse>('/api/health/score')
      .then((res) => setData(res.data))
      .catch(() => setError(true))
  }, [])

  async function handleExplain() {
    if (!data) return
    setExplaining(true)
    setExplanation(null)
    try {
      const res = await api.post('/ai/whatif-commentary', {
        health_score_context: {
          score: data.score,
          band: data.band,
          pillars: data.pillars.map((p) => ({ label: p.label, score: p.score, value: p.value_label })),
        },
      })
      setExplanation(res.data.summary)
    } catch {
      setExplanation("Couldn't generate an explanation right now — try again in a moment.")
    } finally {
      setExplaining(false)
    }
  }

  if (error) {
    return (
      <div className="card-lifted px-6 py-16 text-center text-sm text-muted">
        Couldn't load your financial health score. Your data is unaffected — try refreshing the page.
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    )
  }

  const topLever = data.top_levers[0]

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-heading text-h2 font-bold text-heading">Financial health</h1>
        <p className="mt-1.5 text-sm text-muted">
          A deterministic score computed from your own transaction data — not an AI guess. See the breakdown below.
        </p>
      </div>

      {data.is_provisional && (
        <div className="mb-6 rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] px-4 py-3 text-sm text-[var(--color-warning-ink)]">
          This score is provisional — some pillars couldn't be computed yet, or there isn't much transaction history. It'll firm up as more
          data comes in.
        </div>
      )}

      {data.score === null ? (
        <div className="card-lifted flex flex-col items-center gap-2 px-6 py-16 text-center">
          <EmptyHealthDataArt />
          <p className="text-sm text-muted">Not enough transaction data yet to compute a health score. Add some transactions to get started.</p>
        </div>
      ) : (
        <>
          <div className="mb-11 grid grid-cols-1 items-center gap-6 lg:grid-cols-[280px_1fr]">
            <div className="card-lifted p-6 text-center">
              <HealthGauge score={data.score} />
              <div className="mt-2 font-heading text-h1 font-bold tabular-nums text-heading">{data.score}</div>
              <div className="mt-1 text-sm font-semibold" style={{ color: BAND_COLOR[data.band ?? ''] ?? 'var(--color-muted)' }}>
                {data.band}
              </div>
            </div>

            <div className="card-lifted p-6">
              <div className="font-heading mb-4 text-base font-semibold text-heading">Breakdown</div>
              <div className="space-y-4">
                {data.pillars.map((pillar) => (
                  <div key={pillar.key}>
                    <div className="mb-1 flex items-baseline justify-between text-sm">
                      <span className="font-medium text-heading">{pillar.label}</span>
                      <span className="text-xs text-muted">{pillar.value_label}</span>
                    </div>
                    {pillar.score === null ? (
                      <p className="text-xs text-muted">Couldn't be computed — {pillar.note.toLowerCase()}</p>
                    ) : (
                      <>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-hairline">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${pillar.score}%` }} />
                        </div>
                        <p className="mt-1 text-xs text-secondary">{pillar.note}</p>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mb-11 grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="card p-6">
              <div className="font-heading mb-3 text-base font-semibold text-heading">Top levers</div>
              {data.top_levers.length === 0 ? (
                <p className="text-sm text-muted">Every computable pillar is already maxed out — nothing to prioritize right now.</p>
              ) : (
                <div className="space-y-3">
                  {data.top_levers.map((lever) => (
                    <div key={lever.pillar_key} className="rounded-lg border border-border p-3">
                      <div className="flex items-baseline justify-between">
                        <span className="text-sm font-medium text-heading">{lever.pillar_label}</span>
                        <span className="money text-xs font-semibold text-primary">+{lever.estimated_point_gain} pts</span>
                      </div>
                      <p className="mt-1 text-xs text-secondary">{lever.note}</p>
                    </div>
                  ))}
                </div>
              )}
              {topLever && (
                <Link
                  to="/what-if"
                  className="mt-4 inline-block rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white"
                >
                  Model this in What-If →
                </Link>
              )}
            </div>

            <div className="card p-6">
              <div className="font-heading mb-3 text-base font-semibold text-heading">Explain this</div>
              <p className="mb-3 text-sm text-secondary">Get a plain-language reading of what's driving your score — the AI explains it, it doesn't compute it.</p>
              <button
                onClick={handleExplain}
                disabled={explaining}
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-heading hover:bg-hairline disabled:opacity-50"
              >
                {explaining ? 'Thinking…' : 'Explain this'}
              </button>
              {explanation && (
                <div className="mt-4 rounded-lg p-3" style={{ background: 'var(--color-ai-soft)' }}>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--color-ai-ink)' }}>
                    {explanation}
                  </p>
                </div>
              )}
            </div>
          </div>

          {data.trend.length > 1 && (
            <div className="card p-6">
              <div className="font-heading mb-4 text-base font-semibold text-heading">Score over time</div>
              <div className="flex items-end gap-3">
                {data.trend.map((point) => (
                  <div key={point.month} className="flex flex-1 flex-col items-center gap-1">
                    <div className="flex h-24 w-full items-end">
                      <div className="w-full rounded-t bg-primary" style={{ height: `${Math.max(point.score, 4)}%` }} />
                    </div>
                    <span className="text-[10px] text-muted">{formatMonth(point.month).slice(0, 3)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
