import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Sits inside ProtectedRoute (so `user` is guaranteed) and in front of the
 * AppShell routes: a user who hasn't completed or explicitly skipped the
 * quiz is sent to /onboarding before they can reach the dashboard. */
export function OnboardingGate() {
  const { user } = useAuth()

  if (user && (user.onboarding_status === 'not_started' || user.onboarding_status === 'in_progress')) {
    return <Navigate to="/onboarding" replace />
  }

  return <Outlet />
}
