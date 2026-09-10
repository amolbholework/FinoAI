import { Link, useLocation } from 'react-router-dom'
import { FinoMark } from './FinoMark'
import { FinoConversationView } from './FinoConversationView'
import { useFino } from '../context/FinoContext'

/** Floating launcher + slide-up chat panel, present on every in-app screen.
 * Positioned above the disclaimer bar (never covers it, and the disclaimer
 * stays visible while the panel is open — see index.css's
 * --disclaimer-bar-h) rather than as part of the panel itself, so it can't
 * drift out of sync with the bar's real height.
 *
 * Open/closed state lives in FinoContext (not local state) so other
 * surfaces — e.g. the dashboard's "Ask Fino" quick action — can open the
 * panel without needing a ref into this component. */
export function FinoLauncher() {
  const { panelOpen, openPanel, closePanel } = useFino()
  const location = useLocation()

  if (location.pathname === '/fino') return null

  return (
    <>
      {panelOpen && (
        <div
          className="fixed right-5 z-40 flex w-[380px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-lg border border-hairline bg-card shadow-[var(--shadow-card)]"
          style={{ bottom: 'calc(var(--disclaimer-bar-h) + 76px)', height: 520, maxHeight: 'calc(100vh - var(--disclaimer-bar-h) - 96px)' }}
        >
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="flex items-center gap-2">
              <FinoMark size={22} />
              <span className="font-heading text-sm font-semibold text-heading">Fino</span>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/fino" onClick={closePanel} className="text-xs font-medium text-primary hover:underline">
                Open full page
              </Link>
              <button onClick={closePanel} aria-label="Close" className="text-muted hover:text-heading">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <div className="min-h-0 flex-1">
            <FinoConversationView compact />
          </div>
        </div>
      )}

      <button
        onClick={() => (panelOpen ? closePanel() : openPanel())}
        aria-label={panelOpen ? 'Close Fino' : 'Open Fino'}
        className="fixed right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-card shadow-[var(--shadow-card)] transition hover:shadow-[var(--shadow-card-hover)]"
        style={{ bottom: 'calc(var(--disclaimer-bar-h) + 16px)' }}
      >
        {panelOpen ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-secondary">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <FinoMark size={30} />
        )}
      </button>
    </>
  )
}
