import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatMoney, formatMonth } from '../lib/format'
import { CategoryBreakdown } from '../components/CategoryBreakdown'
import { Skeleton } from '../components/Skeleton'

interface MonthlySummary {
  month: string | null
  total_spend_minor: number
  category_breakdown_minor: Record<string, number>
  income_minor: number
  net_minor: number
  savings_rate_pct: number
}

export function ReportsPage() {
  const currency = useCurrency()
  const [summary, setSummary] = useState<MonthlySummary | null>(null)
  const [months, setMonths] = useState<string[]>([])
  const [selectedMonth, setSelectedMonth] = useState<string>('')

  useEffect(() => {
    api.get('/analysis/monthly-totals').then((res) => setMonths(Object.keys(res.data).sort().reverse()))
  }, [])

  useEffect(() => {
    api.get('/reports/monthly-summary', { params: selectedMonth ? { month: selectedMonth } : {} }).then((res) => {
      setSummary(res.data)
      if (!selectedMonth) setSelectedMonth(res.data.month)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMonth])

  function exportPdf() {
    window.open(`${api.defaults.baseURL}/reports/monthly-summary/export.pdf?month=${selectedMonth}`, '_blank')
  }

  function exportCsv() {
    window.open(`${api.defaults.baseURL}/reports/transactions/export.csv`, '_blank')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-xl font-semibold">Reports</h1>
        <div className="flex gap-2">
          <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm">
            {months.map((m) => (
              <option key={m} value={m}>
                {formatMonth(m)}
              </option>
            ))}
          </select>
          <button onClick={exportCsv} className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-black/[0.02]">
            Export transactions CSV
          </button>
          <button onClick={exportPdf} className="rounded-lg bg-[var(--accent)] px-3 py-1.5 text-sm font-semibold text-white">
            Export PDF summary
          </button>
        </div>
      </div>

      {!summary ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="card-lifted p-6 lg:col-span-1">
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]">{formatMonth(summary.month ?? '')}</p>
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Income</span>
                <span className="tabular-nums font-medium">{formatMoney(summary.income_minor, currency)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Spend</span>
                <span className="tabular-nums font-medium">{formatMoney(summary.total_spend_minor, currency)}</span>
              </div>
              <div className="flex justify-between border-t border-[var(--border)] pt-2">
                <span className="text-[var(--text-secondary)]">Net</span>
                <span className="tabular-nums font-semibold text-[var(--accent)]">{formatMoney(summary.net_minor, currency)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Savings rate</span>
                <span className="tabular-nums font-medium">{summary.savings_rate_pct}%</span>
              </div>
            </div>
          </div>
          <div className="card-lifted p-6 lg:col-span-2">
            <h2 className="font-display mb-4 text-base font-semibold">Spend by category</h2>
            <CategoryBreakdown data={summary.category_breakdown_minor} currency={currency} />
          </div>
        </div>
      )}
    </div>
  )
}
