import { useAuth } from '../context/AuthContext'

/** Persistent, unmissable — shown whenever the account currently being
 * viewed is a demo account (either a "Try demo" guest, or a real account
 * with test mode toggled on). Deliberately not dismissible: the whole
 * point is that a screenshot or screen-share is never ambiguous about
 * whether the numbers on screen are real. */
export function TestModeBanner() {
  const { user } = useAuth()
  const isDemoActive = !!user && (user.is_demo || user.test_mode_enabled)

  if (!isDemoActive) return null

  return (
    <div className="flex items-center justify-center gap-2 bg-warning px-4 py-2 text-center text-xs font-semibold text-white sm:text-sm">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="flex-none">
        <path d="M12 9v4M12 17h.01" />
        <path d="M10.29 3.86l-8.16 14.14A1.5 1.5 0 0 0 3.5 20.5h17a1.5 1.5 0 0 0 1.37-2.5L13.71 3.86a1.5 1.5 0 0 0-2.42 0z" />
      </svg>
      Test Mode — showing sample data
    </div>
  )
}
