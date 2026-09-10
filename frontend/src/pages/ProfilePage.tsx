import { useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ProfileAvatar } from '../components/ProfileAvatar'
import { api } from '../lib/api'

const DELETE_CONFIRM_WORD = 'DELETE'

interface Row {
  label: string
  value?: string
  onClick?: () => void
  soon?: boolean
  toggle?: { checked: boolean; onChange: () => void; busy?: boolean }
}

interface Group {
  title: string
  rows: Row[]
}

export function ProfilePage() {
  const { user, refreshUser, signOut } = useAuth()
  const navigate = useNavigate()
  const [deleting, setDeleting] = useState(false)
  const [togglingDemo, setTogglingDemo] = useState(false)

  if (!user) return null

  async function handleSignOut() {
    await signOut()
    navigate('/')
  }

  async function handleRetakeQuiz() {
    await api.post('/api/onboarding/retake')
    navigate('/onboarding')
  }

  async function handleToggleTestMode() {
    if (!user) return
    setTogglingDemo(true)
    try {
      await api.post(user.test_mode_enabled ? '/api/demo/disable' : '/api/demo/enable')
      await refreshUser()
    } finally {
      setTogglingDemo(false)
    }
  }

  const modeRow: Row = user.is_demo
    ? { label: 'Mode', value: 'Demo account' }
    : {
        label: 'Test mode',
        value: user.test_mode_enabled ? 'Showing sample data' : undefined,
        toggle: { checked: user.test_mode_enabled, onChange: handleToggleTestMode, busy: togglingDemo },
      }

  const groups: Group[] = [
    {
      title: 'Account',
      rows: [
        { label: 'Personal details', soon: true },
        { label: 'Connected Google account', value: user.email },
        modeRow,
        {
          label: 'Retake quiz',
          value: user.onboarding_status === 'skipped' ? 'Skipped' : undefined,
          onClick: handleRetakeQuiz,
        },
      ],
    },
    {
      title: 'Data',
      rows: [
        { label: 'Imported statements', onClick: () => navigate('/import') },
        { label: 'Scanned screenshots', onClick: () => navigate('/import') },
        { label: 'Categories and rules', soon: true },
        { label: 'Export my data', onClick: () => navigate('/reports') },
      ],
    },
    {
      title: 'Preferences',
      rows: [
        { label: 'Currency and number format', soon: true },
        { label: 'Notifications', soon: true },
        { label: 'Appearance', value: 'Light' },
      ],
    },
    {
      title: 'Privacy and security',
      rows: [
        { label: 'Active sessions', soon: true },
        { label: 'Delete my account', onClick: () => setDeleting(true) },
      ],
    },
    {
      title: 'Support',
      rows: [
        { label: 'Help', soon: true },
        { label: 'About FinPilot', soon: true },
        { label: 'Terms and privacy', soon: true },
      ],
    },
  ]

  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-canvas px-5 pt-6 pb-16 sm:static sm:inset-auto sm:z-auto sm:px-0 sm:pt-0">
      <button
        onClick={() => navigate(-1)}
        aria-label="Back"
        className="mb-5 flex h-9 w-9 items-center justify-center rounded-full text-secondary hover:bg-hairline sm:hidden"
      >
        <BackArrowIcon />
      </button>

      <div className="mx-auto max-w-[560px]">
        <div className="mb-9 flex items-center gap-4">
          <ProfileAvatar user={user} size={64} />
          <div className="min-w-0">
            <div className="font-heading truncate text-h4 font-bold text-heading">{user.name}</div>
            <div className="truncate text-sm text-muted">{user.email}</div>
            <div className="mt-1 font-mono text-[11px] text-muted">{user.id}</div>
          </div>
        </div>

        {groups.map((group) => (
          <ProfileGroup key={group.title} title={group.title} rows={group.rows} />
        ))}

        <div className="mt-9 border-t border-hairline pt-6">
          <button
            onClick={handleSignOut}
            className="min-h-14 w-full text-left text-sm font-medium text-overspend"
          >
            Sign out
          </button>
        </div>
      </div>

      {deleting && <DeleteAccountDialog onClose={() => setDeleting(false)} />}
    </div>
  )
}

function ProfileGroup({ title, rows }: Group) {
  return (
    <div className="mb-8">
      <div className="mb-2 px-1 text-caption font-semibold tracking-[0.08em] text-muted uppercase">{title}</div>
      <div className="divide-y divide-hairline rounded-lg border border-hairline bg-card">
        {rows.map((row) => (
          <ProfileRow key={row.label} {...row} />
        ))}
      </div>
    </div>
  )
}

function ProfileRow({ label, value, onClick, soon, toggle }: Row) {
  const interactive = !!onClick
  const destructive = label === 'Delete my account'

  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onClick : undefined}
      onKeyDown={interactive ? (e) => (e.key === 'Enter' || e.key === ' ') && onClick?.() : undefined}
      className={`flex min-h-14 items-center justify-between gap-4 px-4 text-sm ${
        interactive ? 'cursor-pointer hover:bg-hairline/50' : ''
      } ${destructive ? 'text-overspend' : 'text-body'}`}
    >
      <span>{label}</span>
      <span className="flex items-center gap-2 text-muted">
        {value && <span className="text-sm">{value}</span>}
        {soon && (
          <span className="rounded-full bg-hairline px-2 py-0.5 text-[11px] font-medium text-muted">Soon</span>
        )}
        {toggle && (
          <button
            role="switch"
            aria-checked={toggle.checked}
            disabled={toggle.busy}
            onClick={(e) => {
              e.stopPropagation()
              toggle.onChange()
            }}
            className={`relative h-6 w-11 flex-none rounded-full transition-colors disabled:opacity-60 ${
              toggle.checked ? 'bg-warning' : 'bg-hairline'
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                toggle.checked ? 'translate-x-[22px]' : 'translate-x-0.5'
              }`}
            />
          </button>
        )}
        {interactive && !destructive && !toggle && <ChevronIcon />}
      </span>
    </div>
  )
}

function DeleteAccountDialog({ onClose }: { onClose: () => void }) {
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [confirmText, setConfirmText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canDelete = confirmText === DELETE_CONFIRM_WORD && !submitting

  async function handleDelete() {
    if (!canDelete) return
    setSubmitting(true)
    setError(null)
    try {
      await api.delete('/api/auth/me')
      await signOut().catch(() => {})
      navigate('/')
    } catch {
      setError('Something went wrong — your account was not deleted. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-card p-6 shadow-[var(--shadow-card)]">
        <h2 className="font-heading text-h4 font-bold text-heading">Delete your account?</h2>
        <p className="mt-2 text-sm leading-relaxed text-secondary">
          This permanently deletes your account and every transaction, budget, goal, and category you own. This
          can't be undone.
        </p>
        <p className="mt-4 text-sm text-secondary">
          Type <span className="font-mono font-semibold text-heading">{DELETE_CONFIRM_WORD}</span> to confirm.
        </p>
        <input
          autoFocus
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          className="mt-2 w-full rounded-sm border border-border px-3 py-2 text-sm outline-none focus:border-primary"
          placeholder={DELETE_CONFIRM_WORD}
        />
        {error && <p className="mt-2 text-xs text-overspend">{error}</p>}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="rounded-sm px-4 py-2 text-sm font-medium text-secondary hover:bg-hairline"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={!canDelete}
            className="rounded-sm bg-overspend px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {submitting ? 'Deleting…' : 'Delete account'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ChevronIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18l6-6-6-6" />
    </svg>
  )
}

function BackArrowIcon(): ReactNode {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  )
}
