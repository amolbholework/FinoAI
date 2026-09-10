import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../lib/api'
import { useCurrency } from '../lib/currency'
import { formatDate, formatMoney } from '../lib/format'
import { Skeleton } from '../components/Skeleton'
import type { Goal } from '../lib/types'

export function GoalsPage() {
  const currency = useCurrency()
  const [goals, setGoals] = useState<Goal[] | null>(null)
  const [form, setForm] = useState({ name: '', target_amount: '', target_date: '', saved_amount: '' })

  async function load() {
    const res = await api.get<Goal[]>('/goals')
    setGoals(res.data)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    await api.post('/goals', {
      name: form.name,
      target_amount_minor: Math.round(parseFloat(form.target_amount) * 100),
      target_date: form.target_date,
      saved_amount_minor: form.saved_amount ? Math.round(parseFloat(form.saved_amount) * 100) : 0,
    })
    setForm({ name: '', target_amount: '', target_date: '', saved_amount: '' })
    load()
  }

  async function handleDelete(id: string) {
    await api.delete(`/goals/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-xl font-semibold">Goals</h1>

      <form onSubmit={handleCreate} className="card grid grid-cols-2 gap-3 p-4 sm:grid-cols-5">
        <input required placeholder="Goal name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm sm:col-span-2" />
        <input required type="number" step="1" placeholder="Target amount" value={form.target_amount} onChange={(e) => setForm((f) => ({ ...f, target_amount: e.target.value }))} className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm" />
        <input required type="date" value={form.target_date} onChange={(e) => setForm((f) => ({ ...f, target_date: e.target.value }))} className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm" />
        <input type="number" step="1" placeholder="Already saved" value={form.saved_amount} onChange={(e) => setForm((f) => ({ ...f, saved_amount: e.target.value }))} className="rounded-lg border border-[var(--border)] px-2 py-1.5 text-sm" />
        <button type="submit" className="col-span-2 rounded-lg bg-[var(--accent)] px-3 py-1.5 text-sm font-semibold text-white sm:col-span-1">
          Add goal
        </button>
      </form>

      {goals === null ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : goals.length === 0 ? (
        <p className="text-sm text-[var(--text-tertiary)]">No goals yet — add one above.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {goals.map((g) => (
            <div key={g.id} className="card-lifted p-5">
              <div className="flex items-center justify-between">
                <p className="font-display font-semibold text-[var(--text-primary)]">{g.name}</p>
                <button onClick={() => handleDelete(g.id)} className="text-xs text-[var(--text-tertiary)] hover:text-[var(--red)]">
                  Remove
                </button>
              </div>
              <p className="mt-1 text-sm text-[var(--text-secondary)]">
                {formatMoney(g.saved_amount_minor, currency)} of {formatMoney(g.target_amount_minor, currency)} · target {formatDate(g.target_date)}
              </p>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[var(--border)]">
                <motion.div
                  className="h-full rounded-full bg-[var(--accent)]"
                  initial={{ width: 0 }}
                  animate={{ width: `${g.progress_pct}%` }}
                  transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
              <p className="mt-2 text-xs text-[var(--text-tertiary)]">
                {g.progress_pct}% funded
                {g.projected_completion_date
                  ? ` · projected completion ${formatDate(g.projected_completion_date)}`
                  : ' · at the current savings rate, this goal won\'t be reached'}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
