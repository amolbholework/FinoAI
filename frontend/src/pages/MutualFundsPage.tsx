import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Skeleton } from '../components/Skeleton'
import { MutualFundsArt } from '../components/illustrations/MutualFundsArt'
import type { CuratedListResponse, CuratedSchemeSummary, FinoBuddyResponse, RiskBand, SchemeDetail } from '../lib/types'

const RISK_OPTIONS = [
  { value: 'low', label: 'Low — I don\'t want my balance to drop' },
  { value: 'medium', label: 'Medium — some ups and downs are fine' },
  { value: 'high', label: 'High — I can ride out volatility for growth' },
]

// Maps the onboarding quiz's risk_band onto Fino Buddy's own risk_comfort
// scale — a starting suggestion the user can still change freely, not a
// hidden override.
const RISK_BAND_TO_COMFORT: Record<RiskBand, string> = {
  conservative: 'low',
  moderate: 'medium',
  aggressive: 'high',
}

const HORIZON_OPTIONS = [
  { value: 'short', label: 'Under 3 years' },
  { value: 'medium', label: '3–7 years' },
  { value: 'long', label: '7+ years' },
]

function ChangeBadge({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-xs text-muted">—</span>
  const positive = pct >= 0
  return (
    <span
      className={`text-xs font-semibold tabular-nums ${positive ? 'text-[var(--color-positive)]' : 'text-[var(--color-overspend)]'}`}
    >
      {positive ? '+' : ''}
      {pct.toFixed(2)}% <span className="font-normal text-muted">/ 30d</span>
    </span>
  )
}

function SchemeSparkline({ history }: { history: SchemeDetail['history'] }) {
  if (history.length < 2) return null
  const values = history.map((p) => p.nav)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 280
  const height = 60
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width
    const y = height - ((v - min) / range) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="none">
      <polyline points={points.join(' ')} fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SchemeCard({ scheme }: { scheme: CuratedSchemeSummary }) {
  const [open, setOpen] = useState(false)
  const [detail, setDetail] = useState<SchemeDetail | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleToggle() {
    const next = !open
    setOpen(next)
    if (next && !detail) {
      setLoading(true)
      try {
        const res = await api.get<SchemeDetail>(`/api/mutual-funds/${scheme.scheme_code}`)
        setDetail(res.data)
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="card overflow-hidden">
      <button onClick={handleToggle} className="flex w-full items-center gap-4 p-4 text-left">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">{scheme.category_label}</span>
            {scheme.is_stale && <span className="text-[10px] text-muted">stale</span>}
          </div>
          <div className="mt-1 truncate text-sm font-semibold text-heading">{scheme.scheme_name}</div>
        </div>
        <div className="flex-none text-right">
          <div className="money text-sm font-semibold text-heading">₹{scheme.latest_nav.toFixed(2)}</div>
          <ChangeBadge pct={scheme.change_pct_30d} />
        </div>
      </button>
      {open && (
        <div className="border-t border-hairline bg-canvas px-4 py-4">
          {loading || !detail ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <>
              <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
                <span>{detail.fund_house}</span>
                <span>{detail.scheme_category}</span>
                <span>As of {detail.latest_date}</span>
              </div>
              <SchemeSparkline history={detail.history} />
              <p className="mt-2 text-xs text-muted">NAV trend, last {detail.history.length} trading days.</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function FinoBuddy() {
  const { profile } = useAuth()
  const suggestedRisk = profile?.risk_band ? RISK_BAND_TO_COMFORT[profile.risk_band] : null
  const [risk, setRisk] = useState<string | null>(suggestedRisk)
  const [horizon, setHorizon] = useState<string | null>(null)
  const [result, setResult] = useState<FinoBuddyResponse | null>(null)
  const [loading, setLoading] = useState(false)

  async function getMatches() {
    if (!risk || !horizon) return
    setLoading(true)
    try {
      const res = await api.post<FinoBuddyResponse>('/api/mutual-funds/fino-buddy', { risk_comfort: risk, horizon })
      setResult(res.data)
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setRisk(null)
    setHorizon(null)
    setResult(null)
  }

  return (
    <div className="card p-6">
      <div className="mb-1 font-heading text-base font-semibold text-heading">Fino Buddy</div>
      <p className="mb-5 text-sm text-secondary">
        Answer two quick questions and Fino Buddy will point at fund categories that broadly fit — a starting point for research, not a
        recommendation to buy.
      </p>

      {!result ? (
        <div className="space-y-5">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-heading">
              How much risk are you comfortable with?
              {suggestedRisk && risk === suggestedRisk && (
                <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">
                  Pre-filled from your profile
                </span>
              )}
            </div>
            <div className="flex flex-col gap-2">
              {RISK_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setRisk(opt.value)}
                  className={`rounded-sm border px-3.5 py-2.5 text-left text-sm transition-colors ${
                    risk === opt.value ? 'border-primary bg-primary-soft text-heading font-medium' : 'border-border text-body hover:bg-hairline'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-2 text-sm font-medium text-heading">What's your investment time horizon?</div>
            <div className="flex flex-col gap-2">
              {HORIZON_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setHorizon(opt.value)}
                  className={`rounded-sm border px-3.5 py-2.5 text-left text-sm transition-colors ${
                    horizon === opt.value ? 'border-primary bg-primary-soft text-heading font-medium' : 'border-border text-body hover:bg-hairline'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={getMatches}
            disabled={!risk || !horizon || loading}
            className="rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? 'Matching…' : 'Show me matching categories'}
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4 rounded-lg border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] px-4 py-3 text-xs leading-relaxed text-[var(--color-warning-ink)]">
            Educational suggestion only — not investment advice. Fund categories are matched from your answers using a fixed rule, not
            personalized analysis. Always read the scheme information document before investing.
          </div>
          <div className="space-y-2.5">
            {result.schemes.map((scheme) => (
              <SchemeCard key={scheme.scheme_code} scheme={scheme} />
            ))}
          </div>
          <button onClick={reset} className="mt-4 text-sm font-medium text-primary hover:underline">
            Start over
          </button>
        </div>
      )}
    </div>
  )
}

export function MutualFundsPage() {
  const [data, setData] = useState<CuratedListResponse | null>(null)
  const [error, setError] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<CuratedListResponse>('/api/mutual-funds/curated')
      .then((res) => setData(res.data))
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <div className="card-lifted px-6 py-16 text-center text-sm text-muted">
        Couldn't load mutual fund data right now. Try refreshing the page.
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    )
  }

  const categories = Array.from(new Set(data.schemes.map((s) => s.category))).map((cat) => ({
    id: cat,
    label: data.schemes.find((s) => s.category === cat)?.category_label ?? cat,
  }))
  const visibleSchemes = categoryFilter ? data.schemes.filter((s) => s.category === categoryFilter) : data.schemes

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <MutualFundsArt size={44} />
        <div>
          <h1 className="font-heading text-h2 font-bold text-heading">Mutual Funds Sahi Hai</h1>
          <p className="mt-1.5 text-sm text-muted">
            Real-time NAV data across fund categories, for learning — not a recommendation to invest in any specific scheme.
          </p>
        </div>
      </div>
      <p className="mb-8 text-xs text-muted">Source: {data.source}</p>

      <div className="mb-10">
        <div className="mb-3 flex flex-wrap gap-2">
          <button
            onClick={() => setCategoryFilter(null)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
              categoryFilter === null ? 'bg-primary text-white' : 'bg-hairline text-secondary hover:bg-border'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategoryFilter(cat.id)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                categoryFilter === cat.id ? 'bg-primary text-white' : 'bg-hairline text-secondary hover:bg-border'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
        <div className="space-y-2.5">
          {visibleSchemes.map((scheme) => (
            <SchemeCard key={scheme.scheme_code} scheme={scheme} />
          ))}
        </div>
      </div>

      <FinoBuddy />
    </div>
  )
}
