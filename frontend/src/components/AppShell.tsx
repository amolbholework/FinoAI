import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { BrandMark } from './BrandMark'
import { ProfileAvatar } from './ProfileAvatar'
import { FinoLauncher } from './FinoLauncher'
import { TestModeBanner } from './TestModeBanner'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/import', label: 'Import' },
  { to: '/forecast', label: 'Forecast' },
  { to: '/advice', label: 'Advice' },
  { to: '/what-if', label: 'What-if' },
  { to: '/health', label: 'Health' },
  { to: '/learn', label: 'Learn' },
  { to: '/mutual-funds', label: 'Mutual funds' },
  { to: '/news', label: 'News' },
  { to: '/scam-awareness', label: 'Scam safety' },
]

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth()
  return (
    <>
      <NavLink to="/" className="mb-9 px-2" onClick={onNavigate}>
        <BrandMark size={38} />
      </NavLink>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `rounded-sm px-3.5 py-2.5 text-sm transition-colors ${
                isActive ? 'bg-primary font-semibold text-white' : 'text-secondary hover:bg-hairline'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {user && (
        <NavLink
          to="/profile"
          onClick={onNavigate}
          className={({ isActive }) =>
            `mt-4 flex items-center gap-2.5 rounded-sm border-t border-hairline px-2 pt-4 pb-1 transition-colors ${
              isActive ? 'text-heading' : 'text-secondary hover:text-heading'
            }`
          }
        >
          <ProfileAvatar user={user} size={32} />
          <span className="min-w-0 flex-1 truncate text-sm font-medium">{user.name}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-none text-muted">
            <path d="M9 18l6-6-6-6" />
          </svg>
        </NavLink>
      )}
    </>
  )
}

/**
 * 232px fixed left sidebar on desktop (md and up); below that it collapses
 * into a hamburger-triggered off-canvas drawer so the app stays usable down
 * to a 360px viewport. Matches the design system: white surface, 1px
 * hairline right border, logo at 38px, active nav item as a filled indigo
 * pill — the drawer reuses the exact same nav markup, just repositioned.
 */
export function AppShell() {
  const { user } = useAuth()
  const isDemoActive = !!user && (user.is_demo || user.test_mode_enabled)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()

  // Close the drawer automatically on navigation rather than relying on
  // every NavLink's onClick alone — covers back/forward too.
  useEffect(() => setMobileNavOpen(false), [location.pathname])

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <TestModeBanner />

      {/* Subtle whole-shell tint while in demo mode, so a screenshot is
          never ambiguous even if the banner itself gets cropped out. */}
      <div className={`flex flex-1 flex-col md:flex-row ${isDemoActive ? 'bg-warning-soft' : ''}`}>
        {/* Mobile top bar — hidden on md+, where the persistent sidebar takes over. */}
        <div className="flex items-center justify-between border-b border-hairline bg-card px-4 py-3 md:hidden">
          <NavLink to="/">
            <BrandMark size={30} />
          </NavLink>
          <button
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open menu"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-secondary hover:bg-hairline"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
        </div>

        {mobileNavOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <button
              aria-label="Close menu"
              onClick={() => setMobileNavOpen(false)}
              className="absolute inset-0 bg-black/30"
            />
            <aside className="absolute inset-y-0 left-0 flex w-[260px] max-w-[80vw] flex-col bg-card px-5 py-8 shadow-[var(--shadow-card)]">
              <SidebarNav onNavigate={() => setMobileNavOpen(false)} />
            </aside>
          </div>
        )}

        <aside className="sticky top-0 hidden h-screen w-[232px] flex-none flex-col border-r border-hairline bg-card px-5 py-8 md:flex">
          <SidebarNav />
        </aside>

        <main className="min-w-0 max-w-[1360px] flex-1 px-4 pt-6 pb-16 sm:px-6 md:px-10 md:pt-11 md:pb-20 lg:px-14">
          <Outlet />
        </main>

        <FinoLauncher />
      </div>
    </div>
  )
}
