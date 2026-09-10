import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { waitForGoogleIdentity, type GoogleCredentialResponse, type GoogleIdentityError } from '../lib/googleIdentity'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

// GIS's own error `type` values for failures that happen inside the
// widget itself, before our callback ever fires — see
// https://developers.google.com/identity/gsi/web/reference/js-reference#error_callback
const ERROR_MESSAGES: Record<string, string> = {
  popup_failed_to_open: 'Your browser blocked the Google sign-in popup. Allow popups for this site and try again.',
  popup_closed: 'Sign-in was closed before it finished. Try again.',
  unregistered_origin: "This site isn't registered for Google sign-in yet — contact support.",
  suppressed_by_user: 'Google sign-in was previously dismissed. Try again to sign in.',
}
const DEFAULT_ERROR_MESSAGE = 'Could not open Google sign-in. Please try again.'

export function GoogleSignInButton() {
  const { signInWithGoogleToken } = useAuth()
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      setError('Sign-in is not configured yet — VITE_GOOGLE_CLIENT_ID is missing.')
      return
    }

    let cancelled = false

    waitForGoogleIdentity()
      .then((googleId) => {
        if (cancelled || !containerRef.current) return

        googleId.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: async (response: GoogleCredentialResponse) => {
            try {
              await signInWithGoogleToken(response.credential)
            } catch {
              setError('Could not complete sign-in. Please try again.')
            }
          },
          use_fedcm_for_prompt: true,
          use_fedcm_for_button: true,
          error_callback: (err: GoogleIdentityError) => {
            setError(ERROR_MESSAGES[err.type] ?? DEFAULT_ERROR_MESSAGE)
          },
        })
        googleId.renderButton(containerRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'pill',
          width: 320,
        })
      })
      .catch(() => setError('Could not load Google Sign-In. Check your connection and try again.'))

    return () => {
      cancelled = true
    }
  }, [signInWithGoogleToken])

  return (
    <div>
      <div ref={containerRef} className="flex justify-center" />
      {error && <p className="mt-3 text-center text-sm text-overspend">{error}</p>}
    </div>
  )
}
