import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { HeroBrand } from '../components/HeroBrand'
import { BrandMark } from '../components/BrandMark'
import { Reveal } from '../components/Reveal'
import { HeroIllustration } from '../components/illustrations/HeroIllustration'
import { ScamAwarenessArt } from '../components/illustrations/ScamAwarenessArt'
import { DotGridDivider } from '../components/illustrations/DotGridDivider'
import { MeshDivider } from '../components/illustrations/MeshDivider'
import { useAuth } from '../context/AuthContext'
import { useCurrency } from '../lib/currency'
import { formatMoney } from '../lib/format'
import { categoryPillColors } from '../lib/categoryColors'
import { api } from '../lib/api'
import {
  featureBands,
  heroAiTip,
  heroNavItems,
  heroPreview,
  heroStatChips,
  heroTransactions,
  howItWorksSteps,
  privacyClaims,
  reportFraud,
  savingsGoalPct,
  scanExample,
  scanExtractedFields,
  staySafeCards,
  type FeatureBand,
} from '../mockdata/landing'
import './LandingPage.css'

const NAV_LINKS = ['Product', 'Security', 'Pricing']

export function LandingPage() {
  const currency = useCurrency()
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [startingDemo, setStartingDemo] = useState(false)

  async function handleTryDemo() {
    setStartingDemo(true)
    try {
      await api.post('/api/demo/try')
      await refreshUser()
      navigate('/dashboard')
    } finally {
      setStartingDemo(false)
    }
  }

  return (
    <div className="font-body text-body">
      {/* NAV — logo · links · sign in · CTA, left to right. Logo is full
          lockup from 640px up; icon-only glyph below that so it doesn't
          crowd the sign-in/CTA buttons on a phone-width screen. */}
      <div className="mx-auto flex max-w-[1320px] items-center justify-between px-6 py-6 sm:px-12 sm:py-9">
        <Link to="/">
          <span className="hidden sm:inline-flex">
            <BrandMark size={36} />
          </span>
          <span className="inline-flex sm:hidden">
            <BrandMark size={30} iconOnly />
          </span>
        </Link>
        <div className="hidden gap-9 text-[14.5px] text-secondary sm:flex">
          {NAV_LINKS.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <div className="flex items-center gap-4 sm:gap-5">
          {!user && (
            <>
              <button
                onClick={handleTryDemo}
                disabled={startingDemo}
                className="text-sm font-semibold text-secondary hover:text-heading disabled:opacity-60"
              >
                {startingDemo ? 'Starting…' : 'Try demo'}
              </button>
              <Link to="/sign-in" className="text-sm font-semibold text-secondary hover:text-heading">
                Sign in
              </Link>
            </>
          )}
          <Link
            to={user ? '/dashboard' : '/sign-in'}
            className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110 sm:px-5 sm:py-2.5"
          >
            {user ? 'Dashboard' : 'Get started'}
          </Link>
        </div>
      </div>

      {/* HERO */}
      <section className="relative overflow-hidden px-6 pt-16 sm:px-12">
        <div className="hero-mesh pointer-events-none absolute inset-0 z-0" />
        <HeroIllustration className="pointer-events-none absolute inset-0 z-0" />
        <div className="relative z-10 mx-auto max-w-[900px] text-center">
          <HeroBrand />
          <h1 className="font-heading text-[40px] font-bold tracking-tight text-heading sm:text-display">
            See your financial
            <br />
            future before it arrives.
          </h1>
          <p className="mx-auto mt-6 max-w-[520px] text-body-lg text-secondary">
            FinPilot analyzes your spending, forecasts what's ahead, and tells you exactly what to do about it.
          </p>
          <Link
            to={user ? '/dashboard' : '/sign-in'}
            className="mt-9 inline-block rounded-xl bg-primary px-8 py-4 text-base font-semibold text-white shadow-[0_12px_28px_-10px_rgba(67,56,202,0.5)] transition hover:brightness-110"
          >
            Upload a statement
          </Link>
        </div>

        {/* FLOATING DASHBOARD PREVIEW — a poster of the app, not a functional
            copy, so internal type sizes are deliberately smaller than the
            real design-system scale to stay legible at this scale. */}
        <div className="relative z-10 mx-auto mt-16 max-w-[760px]" style={{ perspective: 1800 }}>
          <div
            className="relative overflow-hidden rounded-xl bg-card"
            style={{
              transform: 'rotateX(7deg) rotateY(-9deg) rotateZ(1deg)',
              boxShadow: '0 60px 100px -40px rgba(30,30,45,0.35), 0 20px 40px -20px rgba(30,30,45,0.15)',
            }}
          >
            <div className="flex h-[38px] items-center gap-1.5 border-b border-hairline bg-hairline px-4">
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
            </div>

            <div className="flex">
              {/* NAV STRIP */}
              <div className="w-[92px] flex-none border-r border-hairline px-2.5 py-5">
                <BrandMark size={14} className="mb-5 px-1" iconOnly />
                <div className="flex flex-col gap-1">
                  {heroNavItems.map((item, i) => (
                    <div
                      key={item}
                      className={`rounded-[6px] px-2 py-1.5 text-[9px] font-medium ${
                        i === 0 ? 'bg-primary text-white' : 'text-secondary'
                      }`}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              {/* MAIN */}
              <div className="relative flex-1 px-6 py-5">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <div className="mb-1 text-[11px] text-muted">Total balance</div>
                    <div className="font-heading text-h3 font-bold tracking-tight text-heading tabular-nums">
                      {formatMoney(heroPreview.totalBalanceMinor, currency)}
                    </div>
                    <div className="mt-0.5 text-[10.5px] font-semibold text-positive">
                      +{heroPreview.balanceDeltaPct}% this month
                    </div>
                  </div>
                  <span className="rounded-full bg-primary-soft px-2.5 py-1 text-[10px] font-semibold text-primary">
                    AI Insight
                  </span>
                </div>

                {/* STAT CHIPS */}
                <div className="mb-4 grid grid-cols-3 gap-2">
                  {heroStatChips.map((chip) => (
                    <div key={chip.label} className="rounded-md bg-canvas px-2.5 py-2">
                      <div className="text-[9px] text-muted">{chip.label}</div>
                      <div className="mt-0.5 font-heading text-[12px] font-bold text-heading tabular-nums">
                        {chip.display ?? formatMoney(chip.valueMinor!, currency)}
                      </div>
                    </div>
                  ))}
                </div>

                <HeroChart />

                {/* TRANSACTION LIST */}
                <div className="mt-4 flex flex-col gap-1.5">
                  {heroTransactions.map((tx) => {
                    const pill = categoryPillColors(tx.category)
                    return (
                      <div key={tx.merchant} className="flex items-center justify-between rounded-md py-1">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="truncate text-[11px] font-medium text-body">{tx.merchant}</span>
                          <span
                            className="flex-none rounded-full px-2 py-0.5 text-[9px] font-semibold"
                            style={{ background: pill.bg, color: pill.ink }}
                          >
                            {tx.category}
                          </span>
                          {tx.unusual && (
                            <span className="flex-none rounded-full bg-overspend-soft px-2 py-0.5 text-[9px] font-semibold text-overspend-ink">
                              Unusual
                            </span>
                          )}
                        </div>
                        <span
                          className="flex-none text-[11px] font-semibold tabular-nums"
                          style={{ color: tx.amountMinor > 0 ? 'var(--color-positive)' : 'var(--color-heading)' }}
                        >
                          {formatMoney(tx.amountMinor, currency)}
                        </span>
                      </div>
                    )
                  })}
                </div>

                {/* AI RECOMMENDATION CARD */}
                <div
                  className="absolute -right-3 -bottom-4 w-[200px] rounded-[13px] p-px shadow-[0_20px_40px_-18px_rgba(30,30,40,0.35)]"
                  style={{ background: 'linear-gradient(135deg, var(--color-cyan), var(--color-primary))' }}
                >
                  <div className="rounded-[12px] bg-card px-3.5 py-3">
                    <div className="mb-1 flex items-center gap-1.5">
                      <span
                        className="h-3 w-3 rounded-[3px]"
                        style={{ background: 'linear-gradient(135deg, var(--color-cyan), var(--color-primary))' }}
                      />
                      <span className="text-[8.5px] font-semibold tracking-wide text-primary uppercase">
                        FinPilot suggests
                      </span>
                    </div>
                    <p className="text-[10.5px] leading-snug text-body">{heroAiTip}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURE BANDS */}
      <section className="mx-auto mt-24 max-w-[1320px] px-6 sm:mt-[140px] sm:px-12">
        {featureBands.map((band) => (
          <Reveal key={band.eyebrow}>
            <FeatureRow band={band} />
          </Reveal>
        ))}
      </section>

      {/* HOW IT WORKS */}
      <Reveal>
        <section className="relative mx-auto max-w-[1320px] overflow-hidden px-6 py-20 sm:px-12">
          <DotGridDivider className="pointer-events-none absolute inset-0 z-0" />
          <div className="relative z-10 mb-14 text-center">
            <div className="mb-3.5 text-caption font-semibold tracking-[0.08em] text-primary uppercase">
              How it works
            </div>
            <h2 className="font-heading text-h2 font-bold tracking-tight text-heading">Three steps, start to finish.</h2>
          </div>
          <div className="relative z-10 grid grid-cols-1 gap-12 sm:grid-cols-3">
            {howItWorksSteps.map((step) => (
              <div key={step.number} className="text-center">
                <div className="font-heading mx-auto mb-5 flex h-11 w-11 items-center justify-center rounded-full bg-primary text-[17px] font-bold text-white">
                  {step.number}
                </div>
                <h3 className="font-heading mb-2.5 text-[18px] font-semibold text-heading">{step.title}</h3>
                <p className="mx-auto max-w-[280px] text-[14.5px] leading-relaxed text-secondary">{step.body}</p>
              </div>
            ))}
          </div>
        </section>
      </Reveal>

      {/* SCAN A SCREENSHOT */}
      <Reveal>
        <section className="relative mx-auto max-w-[1320px] overflow-hidden px-6 py-20 sm:px-12">
          <MeshDivider className="pointer-events-none absolute inset-0 z-0" />
          <div className="relative z-10 mb-14 text-center">
            <div className="mb-3.5 text-caption font-semibold tracking-[0.08em] text-primary uppercase">
              Scan a screenshot
            </div>
            <h2 className="font-heading text-h2 font-bold tracking-tight text-heading">
              A payment confirmation in, a transaction out.
            </h2>
            <p className="mx-auto mt-3.5 max-w-[480px] text-base text-secondary">
              UPI success screens, bank SMS, receipts — FinPilot reads the fields for you and asks you to confirm.
            </p>
          </div>

          <div className="relative z-10 mx-auto flex max-w-[720px] flex-col items-center gap-8 sm:flex-row sm:justify-center">
            {/* PHONE MOCKUP */}
            <div className="w-[220px] flex-none rounded-[28px] border-[6px] border-heading bg-card p-1 shadow-[0_30px_60px_-24px_rgba(30,30,40,0.35)]">
              <div className="rounded-[22px] bg-canvas px-4 pt-6 pb-8">
                <div className="mb-4 flex flex-col items-center">
                  <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-full bg-positive-soft">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                      <path d="M5 13l4 4L19 7" stroke="var(--color-positive-ink)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <div className="text-[12px] font-semibold text-positive-ink">{scanExample.status}</div>
                  <div className="mt-0.5 text-[10px] text-muted">via {scanExample.app}</div>
                </div>
                <div className="text-center">
                  <div className="font-heading text-h3 font-bold tabular-nums text-heading">₹450.00</div>
                  <div className="mt-1 text-[12px] text-secondary">Paid to {scanExample.merchant}</div>
                  <div className="mt-3 text-[10px] text-muted">{scanExample.dateLabel}</div>
                  <div className="mt-0.5 text-[9px] text-muted">{scanExample.reference}</div>
                </div>
              </div>
            </div>

            <svg className="hidden flex-none sm:block" width="40" height="24" viewBox="0 0 40 24" fill="none">
              <path d="M2 12h32M26 4l8 8-8 8" stroke="var(--color-cyan)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <svg className="flex-none sm:hidden" width="24" height="32" viewBox="0 0 24 32" fill="none">
              <path d="M12 2v24M4 20l8 8 8-8" stroke="var(--color-cyan)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>

            {/* EXTRACTED FIELDS */}
            <div className="card-lifted w-full max-w-[280px] flex-none p-6">
              <div className="mb-4 flex items-center gap-2">
                <span
                  className="inline-block h-4 w-4 rounded-[4px]"
                  style={{ background: 'linear-gradient(135deg, var(--color-cyan), var(--color-primary))' }}
                />
                <span className="text-[11px] font-semibold tracking-wide text-primary uppercase">Extracted</span>
              </div>
              <div className="flex flex-col gap-3">
                {scanExtractedFields.map((f) => (
                  <div key={f.label} className="flex items-center justify-between border-b border-hairline pb-2.5 last:border-0 last:pb-0">
                    <span className="text-[12px] text-muted">{f.label}</span>
                    <span className="text-[13px] font-semibold text-body">{f.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </Reveal>

      {/* STAY SAFE */}
      <Reveal>
        <section className="relative overflow-hidden rounded-3xl mx-6 sm:mx-12" style={{ background: '#FAF6EF' }}>
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                'radial-gradient(circle at 15% 20%, color-mix(in srgb, var(--color-overspend) 15%, transparent), transparent 55%), radial-gradient(circle at 85% 10%, color-mix(in srgb, var(--color-warning) 20%, transparent), transparent 50%)',
            }}
          />
          <div className="relative px-6 pt-14 sm:px-12">
            <div className="mx-auto mb-10 max-w-[560px] text-center">
              <ScamAwarenessArt className="mx-auto mb-4" />
              <h2 className="font-heading text-h2 font-bold tracking-tight text-heading">Stay safe with FinPilot</h2>
              <p className="mt-2.5 text-[15px] text-secondary">
                Financial scams often impersonate trusted apps. Here's what FinPilot will never ask of you.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {staySafeCards.map((card) => (
                <div key={card.title} className="rounded-lg bg-card p-6 shadow-[0_20px_44px_-26px_rgba(30,30,40,0.12)]">
                  <div className="font-heading mb-2 text-[16px] font-bold text-heading">{card.title}</div>
                  <div className="text-[13.5px] leading-relaxed text-secondary">{card.desc}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="relative mt-11 flex flex-col items-center justify-between gap-4 bg-heading px-6 py-6 sm:flex-row sm:px-12">
            <div>
              <div className="mb-1 text-xs text-white/60">Think you've been targeted? Report it.</div>
              <div className="font-heading text-h3 font-bold tabular-nums text-white">{reportFraud.phone}</div>
            </div>
            <a href={reportFraud.portalUrl} className="text-sm font-semibold text-cyan underline">
              {reportFraud.portal}
            </a>
          </div>
        </section>
      </Reveal>

      {/* PRIVACY STRIP */}
      <Reveal>
        <section className="mx-auto max-w-[1320px] px-6 py-16 sm:px-12">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            {privacyClaims.map((claim) => (
              <div key={claim} className="flex items-start gap-3">
                <svg className="mt-0.5 flex-none" width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" fill="var(--color-positive-soft)" />
                  <path d="M8 12.5l2.5 2.5L16 9" stroke="var(--color-positive-ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="text-[14px] leading-snug text-secondary">{claim}</span>
              </div>
            ))}
          </div>
        </section>
      </Reveal>

      {/* FINAL CTA */}
      <Reveal>
        <section className="relative mx-6 mb-16 overflow-hidden rounded-3xl px-6 py-20 text-center sm:mx-12 sm:px-12">
          <div className="hero-mesh pointer-events-none absolute inset-0 z-0" style={{ opacity: 0.35 }} />
          <div className="relative z-10">
            <h2 className="font-heading text-h1 font-bold tracking-tight text-heading">
              See next month before it starts.
            </h2>
            <p className="mx-auto mt-3.5 max-w-[420px] text-base text-secondary">
              Upload a statement or scan a screenshot — FinPilot does the rest.
            </p>
            <Link
              to={user ? '/dashboard' : '/sign-in'}
              className="mt-8 inline-block rounded-xl bg-primary px-8 py-4 text-base font-semibold text-white shadow-[0_12px_28px_-10px_rgba(67,56,202,0.5)] transition hover:brightness-110"
            >
              Upload a statement
            </Link>
          </div>
        </section>
      </Reveal>

      {/* FOOTER */}
      <footer className="mx-auto flex max-w-[1320px] flex-col items-center gap-4 px-6 pt-12 pb-14 text-center sm:flex-row sm:justify-between sm:px-12 sm:text-left">
        <div className="opacity-85">
          <BrandMark size={18} />
        </div>
        <div className="flex gap-7 text-[13.5px] text-muted">
          <span>Product</span>
          <span>Security</span>
          <span>Contact</span>
        </div>
        <div className="text-[13px] text-muted">© 2026 FinPilot AI</div>
      </footer>
    </div>
  )
}

function FeatureRow({ band }: { band: FeatureBand }) {
  return (
    <div className="grid grid-cols-1 items-center gap-16 border-t border-hairline py-20 last:border-b md:grid-cols-2">
      <div className={band.reverse ? 'md:order-2' : ''}>
        <div className="mb-3.5 text-caption font-semibold tracking-[0.08em] text-primary uppercase">
          {band.eyebrow}
        </div>
        <h3 className="font-heading text-h2 font-bold tracking-tight text-heading">{band.title}</h3>
        <p className="mt-3.5 max-w-[420px] text-base leading-relaxed text-secondary">{band.body}</p>
      </div>
      <div className={`card-lifted p-7 ${band.reverse ? 'md:order-1' : ''}`}>
        <FeatureIllustration kind={band.illustration} />
      </div>
    </div>
  )
}

function HeroChart() {
  const todayX = 380

  return (
    <svg viewBox="0 0 600 110" width="100%" height="100" style={{ overflow: 'visible', display: 'block' }}>
      <line x1="0" y1="20" x2="600" y2="20" stroke="var(--color-hairline)" strokeWidth="1" />
      <line x1="0" y1="55" x2="600" y2="55" stroke="var(--color-hairline)" strokeWidth="1" />
      <line x1="0" y1="90" x2="600" y2="90" stroke="var(--color-hairline)" strokeWidth="1" />

      <line x1={todayX} y1="0" x2={todayX} y2="95" stroke="var(--color-border)" strokeWidth="1.5" strokeDasharray="3,3" />
      <text x={todayX + 5} y="12" fontSize="9" fill="var(--color-muted)" fontFamily="var(--font-body)">
        Today
      </text>

      {/* actual spend, area-filled up to today */}
      <path
        d={`M0,85 C40,78 80,82 120,65 C160,50 200,58 240,42 C280,32 320,45 ${todayX},30 L${todayX},95 L0,95 Z`}
        fill="var(--color-primary)"
        opacity="0.08"
      />
      <path
        d={`M0,85 C40,78 80,82 120,65 C160,50 200,58 240,42 C280,32 320,45 ${todayX},30`}
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx={todayX} cy="30" r="4" fill="var(--color-primary)" />

      {/* forecast continuation, dashed */}
      <path
        d={`M${todayX},30 C420,26 460,18 500,15 C530,13 565,16 600,8`}
        fill="none"
        stroke="var(--color-cyan)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="2,7"
      />
    </svg>
  )
}

function FeatureIllustration({ kind }: { kind: FeatureBand['illustration'] }) {
  if (kind === 'analyze') {
    const bars = [
      { x: 10, y: 60, h: 50, color: 'var(--color-primary)' },
      { x: 55, y: 30, h: 80, color: 'var(--color-primary)' },
      { x: 100, y: 75, h: 35, color: 'var(--color-cyan)' },
      { x: 145, y: 45, h: 65, color: 'var(--color-primary)' },
      { x: 190, y: 85, h: 25, color: 'var(--color-cyan)' },
      { x: 235, y: 20, h: 90, color: 'var(--color-positive)' },
    ]
    return (
      <>
        <div className="mb-4 text-[12.5px] text-muted">Spending by category</div>
        <svg viewBox="0 0 300 120" width="100%" height="120">
          {bars.map((b) => (
            <rect key={b.x} x={b.x} y={b.y} width="28" height={b.h} rx="4" fill={b.color} />
          ))}
        </svg>
      </>
    )
  }

  if (kind === 'forecast') {
    return (
      <>
        <div className="mb-4 text-[12.5px] text-muted">Balance forecast · next 60 days</div>
        <svg viewBox="0 0 300 120" width="100%" height="120">
          <line x1="180" y1="0" x2="180" y2="120" stroke="var(--color-hairline)" strokeWidth="1" strokeDasharray="3,3" />
          <path
            d="M0,90 C40,80 80,85 120,65 C150,52 165,48 180,44"
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M180,44 C210,36 240,42 270,25 C280,20 290,16 300,10"
            fill="none"
            stroke="var(--color-cyan)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="1,7"
          />
          <circle cx="180" cy="44" r="4.5" fill="var(--color-primary)" />
        </svg>
      </>
    )
  }

  return (
    <div className="flex items-center gap-6">
      <svg viewBox="0 0 120 120" width="110" height="110">
        <circle cx="60" cy="60" r="48" fill="none" stroke="var(--color-hairline)" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r="48"
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${(savingsGoalPct / 100) * 301.6} 301.6`}
          transform="rotate(-90 60 60)"
        />
      </svg>
      <div>
        <div className="mb-1.5 text-[12.5px] text-muted">Savings goal on track</div>
        <div className="font-heading text-h3 font-bold text-heading tabular-nums">{savingsGoalPct}%</div>
      </div>
    </div>
  )
}
