/** Shown when the dashboard's data fetch genuinely fails (network error,
 * 5xx) — distinct from the empty state (zero data is not an error). */
export function DashboardErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="card-lifted flex flex-col items-center gap-3 px-6 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-overspend-soft)]">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--color-overspend-ink)]">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16h.01" />
        </svg>
      </div>
      <h2 className="font-heading text-lg font-semibold text-heading">Couldn't load your dashboard</h2>
      <p className="max-w-sm text-sm text-secondary">Something went wrong fetching your data. Your account and transactions are unaffected.</p>
      <button onClick={onRetry} className="mt-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">
        Try again
      </button>
    </div>
  )
}
