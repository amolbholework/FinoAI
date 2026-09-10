interface WhatIfSpotArtProps {
  size?: number
  className?: string
}

/** Small header accent for the What-If page — three lever/slider tracks
 * with handles at different positions, echoing the page's own sliders.
 * Purely decorative, aria-hidden. */
export function WhatIfSpotArt({ size = 40, className = '' }: WhatIfSpotArtProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true" className={className}>
      <rect x="4" y="10" width="32" height="20" rx="10" fill="var(--color-primary-soft)" />
      <line x1="10" y1="15" x2="30" y2="15" stroke="var(--color-primary)" strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round" />
      <circle cx="22" cy="15" r="3" fill="var(--color-primary)" />
      <line x1="10" y1="20" x2="30" y2="20" stroke="var(--color-primary)" strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round" />
      <circle cx="14" cy="20" r="3" fill="var(--color-cyan)" />
      <line x1="10" y1="25" x2="30" y2="25" stroke="var(--color-primary)" strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round" />
      <circle cx="26" cy="25" r="3" fill="var(--color-positive)" />
    </svg>
  )
}
