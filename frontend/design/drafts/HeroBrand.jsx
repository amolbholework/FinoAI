import BrandMark from './BrandMark';
import './HeroBrand.css';

/**
 * HeroBrand — the branding block that sits above the home screen headline.
 * Drop this in as the first child of your hero section.
 */
export default function HeroBrand() {
  return (
    <div className="fp-hero-brand">
      <BrandMark className="fp-hero-brand__mark" size={undefined} />

      <h1 className="fp-hero-brand__wordmark">
        FinPilot<span className="fp-hero-brand__ai">&nbsp;AI</span>
      </h1>

      <p className="fp-hero-brand__tagline">
        See where your money is going — and where it&rsquo;s headed next.
      </p>
    </div>
  );
}
