import { Link } from 'react-router-dom'
import { useFino } from '../context/FinoContext'

const SHELL_CLASS =
  'flex min-w-[45%] flex-1 items-center gap-2.5 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-heading transition hover:border-primary-border hover:bg-primary-soft sm:min-w-0'

function ActionLink({ to, label, icon }: { to: string; label: string; icon: React.ReactNode }) {
  return (
    <Link to={to} className={SHELL_CLASS}>
      {icon}
      {label}
    </Link>
  )
}

function ActionButton({ onClick, label, icon }: { onClick: () => void; label: string; icon: React.ReactNode }) {
  return (
    <button type="button" onClick={onClick} className={SHELL_CLASS}>
      {icon}
      {label}
    </button>
  )
}

const iconProps = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

/** The dashboard's fast paths into the four ways a user actually changes
 * their data or gets help: log a transaction by hand, bring in a statement,
 * scan a screenshot, or ask Fino. Kept as one row of equal-weight actions
 * rather than burying any of them in a menu. */
export function QuickActions() {
  const { openPanel } = useFino()

  return (
    <div className="flex flex-wrap gap-3">
      <ActionLink
        to="/transactions?openAdd=1"
        label="Add expense"
        icon={
          <svg {...iconProps} className="text-primary">
            <path d="M12 5v14M5 12h14" />
          </svg>
        }
      />
      <ActionLink
        to="/import"
        label="Upload statement"
        icon={
          <svg {...iconProps} className="text-primary">
            <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5 5 5M12 5v11" />
          </svg>
        }
      />
      <ActionLink
        to="/import"
        label="Scan a screenshot"
        icon={
          <svg {...iconProps} className="text-primary">
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="M3 15l4.5-4.5a2 2 0 012.8 0L15 15M14 13l1.5-1.5a2 2 0 012.8 0L21 14" />
            <circle cx="8" cy="9" r="1.25" />
          </svg>
        }
      />
      <ActionButton
        onClick={openPanel}
        label="Ask Fino"
        icon={
          <svg {...iconProps} className="text-primary">
            <path d="M12 3a7 7 0 00-7 7c0 2.4 1.2 4.5 3 5.8V19a1 1 0 001 1h6a1 1 0 001-1v-3.2c1.8-1.3 3-3.4 3-5.8a7 7 0 00-7-7z" />
            <path d="M10 21h4" />
          </svg>
        }
      />
    </div>
  )
}
