import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Skeleton } from '../components/Skeleton'
import { EmptyNewsArt } from '../components/illustrations/EmptyNewsArt'
import type { NewsArticle, NewsResponse } from '../lib/types'

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const diffMs = Date.now() - then
  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function ArticleCard({ article }: { article: NewsArticle }) {
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noreferrer"
      className="card flex gap-4 overflow-hidden p-4 transition-shadow hover:shadow-[var(--shadow-card)]"
    >
      {article.image_url && (
        <img
          src={article.image_url}
          alt=""
          className="h-20 w-20 flex-none rounded-lg bg-hairline object-cover"
          onError={(e) => {
            e.currentTarget.style.display = 'none'
          }}
        />
      )}
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2 text-xs text-muted">
          <span className="font-semibold text-secondary">{article.source}</span>
          <span>·</span>
          <span>{timeAgo(article.published_at)}</span>
        </div>
        <div className="text-sm font-semibold leading-snug text-heading">{article.title}</div>
        {article.description && <p className="mt-1 line-clamp-2 text-xs text-secondary">{article.description}</p>}
      </div>
    </a>
  )
}

export function FinanceNewsPage() {
  const [data, setData] = useState<NewsResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    api
      .get<NewsResponse>('/api/news')
      .then((res) => setData(res.data))
      .catch(() => setError(true))
  }, [])

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-heading text-h2 font-bold text-heading">Finance news</h1>
        <p className="mt-1.5 text-sm text-muted">A filtered feed of finance and markets headlines — cached, not real-time to the second.</p>
      </div>

      {error || (data && !data.is_available) ? (
        <div className="card-lifted flex flex-col items-center gap-2 px-6 py-16 text-center">
          <EmptyNewsArt />
          <p className="text-sm text-muted">
            News is temporarily unavailable — the feed provider isn't configured or didn't respond. The rest of the app is unaffected.
          </p>
        </div>
      ) : !data ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : (
        <>
          {data.is_stale && (
            <div className="mb-6 rounded-xl border border-[var(--color-warning)]/25 bg-[var(--color-warning-soft)] px-4 py-3 text-sm text-[var(--color-warning-ink)]">
              Showing the last successfully fetched headlines — the feed provider didn't respond just now.
            </div>
          )}
          <div className="space-y-3">
            {data.articles.map((article) => (
              <ArticleCard key={article.uuid} article={article} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
