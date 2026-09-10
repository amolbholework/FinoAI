import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatMoney } from '../lib/format'
import { Skeleton } from '../components/Skeleton'
import type { Budget, BudgetAdherence, Category } from '../lib/types'

export function BudgetsPage() {
  const currency = useCurrency()
  const [budgets, setBudgets] = useState<Budget[] | null>(null)
  const [adherence, setAdherence] = useState<Record<string, BudgetAdherence>>({})
  const [categories, setCategories] = useState<Category[]>([])
  const [newBudget, setNewBudget] = useState({ category_id: '', amount: '' })

  async function load() {
    const [budgetsRes, adherenceRes, categoriesRes] = await Promise.all([
      api.get<Budget[]>('/budgets'),
      api.get<BudgetAdherence[]>('/analysis/budget-adherence'),
      api.get<Category[]>('/categories'),
    ])
    setBudgets(budgetsRes.data)
    setAdherence(Object.fromEntries(adherenceRes.data.map((a) => [a.category, a])))
    setCategories(categoriesRes.data)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSetBudget(e: React.FormEvent) {
    e.preventDefault()
    if (!newBudget.category_id || !newBudget.amount) return
    await api.put('/budgets', { category_id: newBudget.category_id, monthly_limit_minor: Math.round(parseFloat(newBudget.amount) * 100) })
    setNewBudget({ category_id: '', amount: '' })
    load()
  }

  async function handleDelete(id: string) {
    await api.delete(`/budgets/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-xl font-semibold">Budgets</h1>

      <form onSubmit={handleSetBudget} className="card flex flex-wrap items-end gap-3 p-4">
        <label className="text-xs">
          <span className="mb-1 block font-medium text-[var(--text-secondary)]">Category</span>
          <select value={newBudget.category_id} onChange={(e) => setNewBudget((b) => ({ ...b, category_id: e.target.value }))} className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm">
            <option value="">Select…</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs">
          <span className="mb-1 block font-medium text-[var(--text-secondary)]">Monthly limit</span>
          <input type="number" step="1" value={newBudget.amount} onChange={(e) => setNewBudget((b) => ({ ...b, amount: e.target.value }))} className="w-32 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm" />
        </label>
        <button type="submit" className="rounded-lg bg-[var(--accent)] px-4 py-1.5 text-sm font-semibold text-white">
          Set budget
        </button>
      </form>

      {budgets === null ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : budgets.length === 0 ? (
        <p className="text-sm text-[var(--text-tertiary)]">No budgets set yet — add one above.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {budgets.map((b) => {
            const a = b.category_name ? adherence[b.category_name] : undefined
            const pct = Math.min(100, a?.pct_used ?? 0)
            const isOver = a?.is_over ?? false
            return (
              <div key={b.id} className="card p-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-[var(--text-primary)]">{b.category_name}</p>
                  <button onClick={() => handleDelete(b.id)} className="text-xs text-[var(--text-tertiary)] hover:text-[var(--red)]">
                    Remove
                  </button>
                </div>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">
                  {formatMoney(a?.spent_minor ?? 0, currency)} of {formatMoney(b.monthly_limit_minor, currency)}
                </p>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[var(--border)]">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: isOver ? 'var(--red)' : 'var(--accent)' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
                {isOver && <p className="mt-1 text-xs font-medium text-[var(--red)]">Over budget this month</p>}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
