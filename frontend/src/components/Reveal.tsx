import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

/**
 * Fade-and-rise reveal for a whole section as it scrolls into view — one
 * reveal per section, not per element inside it. Matches HeroBrand's
 * 600ms ease-out. `useReducedMotion` makes this a no-op (renders visible,
 * no animation) for prefers-reduced-motion, same as HeroBrand's own
 * @media query.
 */
export function Reveal({ children, className = '' }: { children: ReactNode; className?: string }) {
  const reduceMotion = useReducedMotion()

  if (reduceMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}
