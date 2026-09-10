// Minimal surface of the Google Identity Services global we actually use.
// The script itself is loaded via a <script> tag in index.html (not an npm
// package — that's how GIS is meant to be consumed), so this just types it.
export interface GoogleCredentialResponse {
  credential: string // the ID token — this is what the backend verifies
}

export interface GoogleIdentityError {
  type: string
}

interface GoogleAccountsIdConfig {
  client_id: string
  callback: (response: GoogleCredentialResponse) => void
  // Opts the button and One Tap prompt into FedCM (the browser's native
  // identity-credential dialog) instead of GIS's legacy window.open()
  // popup. The legacy popup is what Google Cloud Console's "project
  // checkup" flags as an insecure flow, and it's what modern Chrome
  // increasingly blocks outright — FedCM avoids that failure mode
  // entirely rather than working around it.
  use_fedcm_for_prompt?: boolean
  use_fedcm_for_button?: boolean
  // Fires for failures that happen inside GIS itself (FedCM unsupported,
  // popup blocked, user dismissed the dialog, etc) — cases that never
  // reach `callback` at all, so without this they fail silently.
  error_callback?: (error: GoogleIdentityError) => void
}

interface GoogleAccountsId {
  initialize(config: GoogleAccountsIdConfig): void
  renderButton(parent: HTMLElement, options: Record<string, unknown>): void
  prompt(): void
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } }
  }
}

/** Resolves once window.google.accounts.id is available. The script tag has
 * async/defer, so it may not have finished loading yet when a component
 * mounts — this polls briefly rather than assuming it's already there. */
export function waitForGoogleIdentity(timeoutMs = 8000): Promise<GoogleAccountsId> {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = () => {
      if (window.google?.accounts?.id) {
        resolve(window.google.accounts.id)
        return
      }
      if (Date.now() - start > timeoutMs) {
        reject(new Error('Google Identity Services failed to load.'))
        return
      }
      setTimeout(check, 100)
    }
    check()
  })
}
