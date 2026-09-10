# FinPilot artwork

Drop this folder in as `src/assets/art/`.

Every illustration is drawn against CSS custom properties with hardcoded fallbacks, so
they inherit your theme once these tokens exist and still render standalone if they don't.

```css
:root {
  --fp-ink:   #10302B;  /* text, needles, outlines            */
  --fp-pine:  #1C5A4E;  /* primary surface + brand            */
  --fp-mint:  #7FD4B8;  /* positive / healthy                 */
  --fp-gold:  #E8A33D;  /* reserved: money out + AI-generated */
  --fp-paper: #F7F5EF;  /* page background                    */
  --fp-slate: #93A5A0;  /* secondary text, muted data         */
}
```

**Important:** CSS variables only reach the SVG if it's inlined or imported as a React
component (`import { ReactComponent as Hero } from './hero-dashboard.svg'`).
An `<img src="...">` renders it in an isolated document and the variables won't resolve —
you'll get the fallback colors instead. That's fine for the empty states, not for the gauge.

| File | Where it goes |
|---|---|
| `logo-mark.svg` | Header, favicon source, loading screen |
| `hero-dashboard.svg` | Landing / onboarding, dashboard empty state |
| `empty-no-data.svg` | Dashboard and transactions before first upload |
| `empty-no-advice.svg` | Advice page before the first advice run |
| `health-gauge.svg` | Financial health checker |
| `fino-avatar.svg` | Fino chat bubble and launcher |

## Driving the gauge

The needle is a `<g transform="rotate(...)">`. Angle is `score * 1.8`, so 0 → 0°,
50 → 90°, 100 → 180°. In React, pass the score in and animate the rotation with a
CSS transition on `transform` — and skip the transition under `prefers-reduced-motion`.

The four arcs are the four bands in order: Needs attention, Getting there, Stable, Strong.
Keep that color assignment consistent with the rest of the app, and don't use red anywhere
in the health checker — the low band is muted slate, deliberately.
