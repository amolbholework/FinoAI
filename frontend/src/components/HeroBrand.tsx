import './HeroBrand.css'
import { BrandMark } from './BrandMark'

/**
 * Brand lockup for the landing hero, above the headline. Kept small (28px)
 * on purpose — the 76px "See your financial future before it arrives"
 * headline is the dominant element on the page, not the logo.
 */
export function HeroBrand() {
  return (
    <div className="hero-brand">
      <BrandMark size={28} />
    </div>
  )
}
