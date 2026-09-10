import { Link } from 'react-router-dom'
import { EmptyTransactionsArt } from './illustrations/EmptyTransactionsArt'

/** Shown when a signed-in user has zero transactions — a fresh real account,
 * not a loading or error state. Points straight at the two ways to get
 * data in rather than showing empty charts with nothing to explain them. */
export function DashboardEmptyState() {
  return (
    <div className="card-lifted flex flex-col items-center gap-3 px-6 py-16 text-center">
      <EmptyTransactionsArt />
      <h2 className="font-heading text-lg font-semibold text-heading">No transactions yet</h2>
      <p className="max-w-sm text-sm text-secondary">
        Add a transaction, upload a bank statement, or scan a payment screenshot to see your spending here.
      </p>
      <div className="mt-2 flex flex-wrap justify-center gap-3">
        <Link to="/transactions?openAdd=1" className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">
          Add a transaction
        </Link>
        <Link to="/import" className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-secondary hover:bg-hairline">
          Upload a statement
        </Link>
      </div>
    </div>
  )
}
