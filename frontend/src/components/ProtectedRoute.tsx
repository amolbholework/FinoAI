import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Unauthenticated users land on sign-in and return to where they were
 * headed afterward. The loading check matters: without it, a page refresh
 * on a protected route would flash the sign-in screen for a moment while
 * the session check is still in flight. */
export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return null

  if (!user) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
