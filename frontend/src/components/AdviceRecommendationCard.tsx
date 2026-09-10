import { formatMoney } from '../lib/format'
import type { AdviceRecommendation } from '../lib/types'

const EFFORT_LABEL: Record<string, string> = { low: 'Low effort', medium: 'Medium effort', high: 'High effort' }
const CATEGORY_LABEL: Record<string, string> = { budget: 'Budget', save: 'Save', invest: 'Invest', debt: 'Debt' }

interface AdviceRecommendationCardProps {
  recommendation: AdviceRecommendation
  currency: string
  onStatusChange: (id: string, status: 'pending' | 'dismissed' | 'done') => void
  onAskFino: (recommendation: AdviceRecommendation) => void
  isTopPriority?: boolean
}

/** One recommendation from POST /api/advice — action, reason, and the
 * estimated monthly rupee impact, with dismiss/done controls that persist
 * server-side. Marked with the AI accent so it's never mistaken for a
 * fact the app itself asserts. */
export function AdviceRecommendationCard({
  recommendation,
  currency,
  onStatusChange,
  onAskFino,
  isTopPriority,
}: AdviceRecommendationCardProps) {
  const isInactive = recommendation.status !== 'pending'

  return (
    <div
      className="rounded-xl border p-4 transition"
      style={{
        borderColor: isInactive ? 'var(--color-border)' : 'var(--color-ai)',
        background: isInactive ? 'var(--color-card)' : 'var(--color-ai-soft)',
        opacity: recommendation.status === 'dismissed' ? 0.55 : 1,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide" style={{ background: 'var(--color-ai)', color: 'white' }}>
              AI
            </span>
            {isTopPriority && (
              <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white" style={{ background: 'var(--color-primary)' }}>
                Top priority
              </span>
            )}
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted">{CATEGORY_LABEL[recommendation.category]}</span>
            <span className="text-[10px] text-muted">·</span>
            <span className="text-[10px] font-medium text-muted">{EFFORT_LABEL[recommendation.effort]}</span>
          </div>
          <p className={`text-sm font-semibold ${recommendation.status === 'done' ? 'text-muted line-through' : 'text-heading'}`}>
            {recommendation.action}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-secondary">{recommendation.why}</p>
          {recommendation.linked_goal && (
            <p className="mt-1.5 text-xs font-medium" style={{ color: 'var(--color-positive-ink)' }}>
              → {recommendation.linked_goal}
              {recommendation.goal_impact ? `: ${recommendation.goal_impact}` : ''}
            </p>
          )}
        </div>
        <div className="flex-none text-right">
          <p className="money text-sm font-semibold" style={{ color: 'var(--color-ai-ink)' }}>
            {recommendation.impact_inr_per_month >= 0 ? '+' : ''}
            {formatMoney(Math.round(recommendation.impact_inr_per_month * 100), currency)}
          </p>
          <p className="text-[10px] text-muted">est. / month</p>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-3 border-t border-hairline pt-2.5">
        {recommendation.status === 'pending' && (
          <>
            <button onClick={() => onStatusChange(recommendation.id, 'done')} className="text-xs font-medium text-primary hover:underline">
              Mark done
            </button>
            <button onClick={() => onStatusChange(recommendation.id, 'dismissed')} className="text-xs font-medium text-muted hover:text-heading">
              Dismiss
            </button>
          </>
        )}
        {recommendation.status !== 'pending' && (
          <>
            <span className="text-xs text-muted">{recommendation.status === 'done' ? 'Marked done' : 'Dismissed'}</span>
            <button onClick={() => onStatusChange(recommendation.id, 'pending')} className="text-xs font-medium text-primary hover:underline">
              Undo
            </button>
          </>
        )}
        <button onClick={() => onAskFino(recommendation)} className="ml-auto text-xs font-medium text-primary hover:underline">
          Why this?
        </button>
      </div>
    </div>
  )
}
