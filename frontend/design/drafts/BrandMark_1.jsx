/**
 * BrandMark — FinPilot AI logo mark.
 *
 * A paper plane whose two wings double as the two segments of a rising
 * trend line. Swap this whole file for an <img src={logo} /> once the
 * final asset exists; nothing else in the app needs to change.
 *
 * Colors come from CSS custom properties so the mark inherits your token
 * file. The fallbacks only apply if a token is missing.
 */
export default function BrandMark({ size = 96, className = '', title = 'FinPilot AI' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={title}
      className={className}
    >
      <defs>
        <linearGradient id="fp-wing" x1="12" y1="60" x2="88" y2="12" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="var(--color-primary, #3730A3)" />
          <stop offset="100%" stopColor="var(--color-accent, #22D3EE)" />
        </linearGradient>
      </defs>

      {/* Flight trail — reads as prior months on a trend line */}
      <g stroke="var(--color-accent, #22D3EE)" strokeWidth="4" strokeLinecap="round" opacity="0.35">
        <path d="M8 84 L18 78" />
        <path d="M24 74 L36 67" />
      </g>

      {/* Upper wing */}
      <path d="M88 12 L12 48 L46 60 Z" fill="url(#fp-wing)" />

      {/* Lower wing, folded — deliberately darker so the fold reads at 32px */}
      <path d="M88 12 L46 60 L40 88 Z" fill="var(--color-primary, #3730A3)" />
    </svg>
  );
}
