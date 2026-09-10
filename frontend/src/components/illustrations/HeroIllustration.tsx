interface HeroIllustrationProps {
  className?: string
}

/** Decorative signature art for the landing hero — an orbit ring, a rupee
 * mark, a small upward trend line, and a scatter of sparkles (the same
 * diamond motif as FinoMark), all drawn in the cyan→indigo brand gradient
 * plus the hero mesh's violet/gold accents so it reads as part of the same
 * family as .hero-mesh rather than a competing graphic. Meant to sit behind
 * the hero copy as a low-opacity background layer, the same way .hero-mesh
 * already does — purely decorative, so it's aria-hidden. */
export function HeroIllustration({ className = '' }: HeroIllustrationProps) {
  return (
    <svg
      viewBox="0 0 800 460"
      width="100%"
      height="100%"
      fill="none"
      aria-hidden="true"
      className={className}
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <linearGradient id="hero-illo-grad" x1="120" y1="60" x2="680" y2="400" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--color-cyan)" />
          <stop offset="1" stopColor="var(--color-primary)" />
        </linearGradient>
      </defs>

      {/* orbit ring, upper-left */}
      <circle cx="150" cy="110" r="86" stroke="var(--color-primary)" strokeOpacity="0.16" strokeWidth="1.5" strokeDasharray="2 8" />
      <circle cx="150" cy="110" r="86" stroke="url(#hero-illo-grad)" strokeOpacity="0.35" strokeWidth="2" strokeDasharray="1 220" strokeLinecap="round" />

      {/* rupee mark, upper-right, soft */}
      <text x="668" y="130" fontSize="64" fontFamily="var(--font-heading)" fontWeight="700" fill="url(#hero-illo-grad)" opacity="0.14">
        ₹
      </text>

      {/* small upward trend, lower-left */}
      <path
        d="M70 400 C110 390 140 405 175 375 C205 350 225 360 255 320"
        stroke="var(--color-positive)"
        strokeOpacity="0.3"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="255" cy="320" r="4.5" fill="var(--color-positive)" fillOpacity="0.4" />

      {/* sparkle scatter, same diamond motif as FinoMark */}
      <path d="M700 300l3.6 8 8 3.6-8 3.6-3.6 8-3.6-8-8-3.6 8-3.6z" fill="var(--color-mesh-gold)" opacity="0.55" />
      <path d="M620 60l2.6 5.8 5.8 2.6-5.8 2.6-2.6 5.8-2.6-5.8-5.8-2.6 5.8-2.6z" fill="var(--color-cyan)" opacity="0.5" />
      <path d="M60 220l2 4.4 4.4 2-4.4 2-2 4.4-2-4.4-4.4-2 4.4-2z" fill="var(--color-mesh-violet)" opacity="0.45" />
    </svg>
  )
}
