import type { AuthUser } from '../lib/types'

function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

/** Circular avatar: the user's Google picture, or an indigo initials fallback. */
export function ProfileAvatar({ user, size = 32 }: { user: AuthUser; size?: number }) {
  if (user.picture_url) {
    return (
      <img
        src={user.picture_url}
        alt=""
        className="flex-none rounded-full object-cover"
        style={{ width: size, height: size }}
        referrerPolicy="no-referrer"
      />
    )
  }
  return (
    <span
      className="flex flex-none items-center justify-center rounded-full bg-primary font-heading font-bold text-white"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {initials(user.name)}
    </span>
  )
}
