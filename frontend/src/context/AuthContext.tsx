import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'
import type { AuthUser, OnboardingProfile } from '../lib/types'

interface AuthContextValue {
  user: AuthUser | null
  // The onboarding-derived personalization profile (risk_band,
  // literacy_level, etc). Null until a user is signed in, and its fields
  // stay null themselves until the quiz is completed or skipped — every
  // consumer treats a null field as "no personalization signal", same as
  // today's un-personalized behavior, never as an error.
  profile: OnboardingProfile | null
  // True only while the initial session check (GET /api/auth/me) is in
  // flight — callers use this to avoid flashing the sign-in screen before
  // we actually know whether there's a valid session.
  loading: boolean
  signInWithGoogleToken: (idToken: string) => Promise<void>
  signOut: () => Promise<void>
  // Re-fetches /api/auth/me and the onboarding profile — used after
  // completing/skipping/retaking onboarding so both update without a full
  // page reload.
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [profile, setProfile] = useState<OnboardingProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    try {
      const res = await api.get<AuthUser>('/api/auth/me')
      setUser(res.data)
      try {
        const profileRes = await api.get<OnboardingProfile>('/api/onboarding/profile')
        setProfile(profileRes.data)
      } catch {
        setProfile(null)
      }
    } catch {
      setUser(null)
      setProfile(null)
    }
  }, [])

  useEffect(() => {
    fetchMe().finally(() => setLoading(false))
  }, [fetchMe])

  async function signInWithGoogleToken(idToken: string) {
    const res = await api.post<AuthUser>('/api/auth/google', { id_token: idToken })
    setUser(res.data)
  }

  async function signOut() {
    try {
      await api.post('/api/auth/logout')
    } finally {
      setUser(null)
      setProfile(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, profile, loading, signInWithGoogleToken, signOut, refreshUser: fetchMe }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
