import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { DISCLAIMER_CONDENSED, DISCLAIMER_FULL, DISCLAIMER_FULL_ROUTE_PREFIXES } from '../config/disclaimer'

/**
 * Persistent, non-dismissible regulatory disclaimer. Mounted once at the
 * root layout (see App.tsx) as a fixed bar so it renders over every page,
 * modal, and the Fino panel without each of them needing to know about it.
 * `body` reserves --disclaimer-bar-h of bottom padding (index.css) so it
 * never covers page content.
 *
 * No mobile bottom tab bar exists in this app yet — when one is added,
 * dock this bar above it rather than at bottom:0 on small screens.
 */
export function DisclaimerBar() {
  const location = useLocation()
  const [expanded, setExpanded] = useState(false)

  const showFull = DISCLAIMER_FULL_ROUTE_PREFIXES.some((prefix) => location.pathname.startsWith(prefix))

  return (
    <div className="fixed inset-x-0 bottom-0 z-[60]">
      {expanded && !showFull && (
        <div className="border-t border-hairline bg-card px-4 py-3 text-xs leading-relaxed text-secondary sm:px-8">
          <div className="mx-auto max-w-[1360px]">{DISCLAIMER_FULL}</div>
        </div>
      )}

      <div className="flex min-h-[var(--disclaimer-bar-h)] items-center border-t border-hairline bg-card px-4 py-2 sm:px-8">
        <div className="mx-auto flex w-full max-w-[1360px] items-center gap-3">
          <p className="flex-1 text-[11px] leading-snug text-muted sm:text-xs">
            {showFull ? DISCLAIMER_FULL : DISCLAIMER_CONDENSED}
          </p>
          {!showFull && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="flex-none text-[11px] font-semibold text-primary hover:underline sm:text-xs"
            >
              {expanded ? 'Hide' : 'Read full disclaimer'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
