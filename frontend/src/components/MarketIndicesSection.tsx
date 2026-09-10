import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { Skeleton } from './Skeleton'
import type { IndexData, MarketIndicesResponse } from '../lib/types'

const POLL_MS = 60_000

export function MarketIndicesSection() {
  const [data, setData] = useState<MarketIndicesResponse | null>(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<number | null>(null)

  async function fetchIndices() {
    try {
      const res = await api.get<MarketIndicesResponse>('/markets/indices')
      setData(res.data)
      setError(false)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIndices()

    function tick() {
      if (document.visibilityState === 'visible') fetchIndices()
    }
    intervalRef.current = window.setInterval(tick, POLL_MS)

    // Refresh immediately when the user comes back to the tab, rather than
    // waiting up to 60s to show a figure that's been stale the whole time
    // they were away.
    function onVisibilityChange() {
      if (document.visibilityState === 'visible') fetchIndices()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [])

  if (loading) {
    return (
      <div className="card-lifted p-6">
        <Skeleton className="mb-4 h-4 w-32" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </div>
    )
  }

  if (error || !data || data.indices.length === 0) {
    return (
      <div className="card-lifted p-6 text-center">
        <div className="font-heading text-sm font-semibold text-heading">Market data unavailable</div>
        <p className="mt-1 text-xs text-muted">Couldn't reach the market data provider right now.</p>
      </div>
    )
  }

  const latestTimestamp = Math.max(...data.indices.map((i) => i.timestamp))
  const anyStale = data.indices.some((i) => i.is_stale)

  return (
    <div className="card-lifted p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-heading text-base font-semibold text-heading">Markets</h2>
        {anyStale && (
          <span className="rounded-full bg-warning-soft px-2.5 py-1 text-[10px] font-semibold text-warning-ink">
            Showing last updated data
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {data.indices.map((idx) => (
          <IndexCard key={idx.symbol} index={idx} />
        ))}
      </div>

      <p className="mt-4 text-[11.5px] text-muted">
        Updated {formatTime(latestTimestamp)} · Delayed by up to {data.delayed_minutes} minutes · Source: {data.source}
      </p>
    </div>
  )
}

function IndexCard({ index }: { index: IndexData }) {
  const isUp = index.change >= 0
  const color = isUp ? 'var(--color-positive)' : 'var(--color-overspend)'

  return (
    <div className="rounded-md bg-canvas p-5">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[13px] font-medium text-secondary">{index.name}</span>
        {!index.is_open && <span className="text-[10.5px] text-muted">Last close</span>}
      </div>
      <div className="font-heading text-h4 font-bold tabular-nums text-heading">
        {index.current.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
      </div>
      <div className="mt-0.5 flex items-center gap-2 text-[12.5px] font-semibold tabular-nums" style={{ color }}>
        <span>
          {isUp ? '+' : ''}
          {index.change.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
        </span>
        <span>
          ({isUp ? '+' : ''}
          {index.change_pct.toFixed(2)}%)
        </span>
      </div>
      <Sparkline points={index.points} color={color} />
    </div>
  )
}

function Sparkline({ points, color }: { points: { value: number }[]; color: string }) {
  if (points.length < 2) return null

  const values = points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 220
  const height = 40

  const path = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width
      const y = height - ((v - min) / range) * height
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="40" className="mt-2" style={{ overflow: 'visible' }}>
      <path d={path} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function formatTime(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleTimeString('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata',
    timeZoneName: 'short',
  })
}
