import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import { BrandMark } from '../components/BrandMark'
import { api } from '../lib/api'

export function SignInPage() {
  const { user, loading, refreshUser } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'
  const [startingDemo, setStartingDemo] = useState(false)

  if (loading) return null
  if (user) return <Navigate to={from} replace />

  async function handleTryDemo() {
    setStartingDemo(true)
    try {
      await api.post('/api/demo/try')
      await refreshUser()
      navigate('/dashboard')
    } finally {
      setStartingDemo(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm rounded-lg bg-card p-9 text-center shadow-[var(--shadow-card)]">
        <div className="mb-6 flex justify-center">
          <BrandMark size={28} />
        </div>

        <h1 className="font-heading text-h4 font-bold text-heading">Sign in to see your financial future</h1>

        <div className="mt-7 mb-5">
          <GoogleSignInButton />
        </div>

        <button
          onClick={handleTryDemo}
          disabled={startingDemo}
          className="mb-6 text-sm font-medium text-primary hover:underline disabled:opacity-60"
        >
          {startingDemo ? 'Starting demo…' : 'Or try a demo — no sign-in needed'}
        </button>

        <p className="text-xs leading-relaxed text-muted">
          We only read your name, email, and profile picture — never your Gmail, Drive, or any bank account.
        </p>
      </div>
    </div>
  )
}
