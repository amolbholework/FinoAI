// Marketing copy + decorative preview figures for the landing page. Kept out
// of the JSX so a later pass can swap the preview numbers for a real
// snapshot from the API without touching layout code.

export const heroPreview = {
  totalBalanceMinor: 4_821_000, // matches the design reference's $48,210 preview figure
  balanceDeltaPct: 2.4,
}

export const heroNavItems = ['Dashboard', 'Import', 'Forecast', 'Advice', 'What-if']

export interface HeroStatChip {
  label: string
  valueMinor?: number
  display?: string
}

export const heroStatChips: HeroStatChip[] = [
  { label: 'Spent this month', valueMinor: 341_200 },
  { label: 'Projected month-end', valueMinor: 489_000 },
  { label: 'Savings rate', display: '22%' },
]

export interface HeroTransaction {
  merchant: string
  category: string
  amountMinor: number
  unusual?: boolean
}

export const heroTransactions: HeroTransaction[] = [
  { merchant: 'Whole Foods Market', category: 'Groceries', amountMinor: -8640 },
  { merchant: 'Delta Air Lines', category: 'Travel', amountMinor: -61200, unusual: true },
  { merchant: 'Paycheck deposit', category: 'Income', amountMinor: 320000 },
]

export const heroAiTip = 'Move ₹3,000 to savings this week — your cash flow forecast shows a surplus through October.'

export interface FeatureBand {
  eyebrow: string
  title: string
  body: string
  illustration: 'analyze' | 'forecast' | 'advise'
  reverse?: boolean
}

export const featureBands: FeatureBand[] = [
  {
    eyebrow: 'Analyze',
    title: 'Every transaction, understood.',
    body: 'FinPilot reads every transaction across your accounts and sorts it into categories automatically, no manual tagging required.',
    illustration: 'analyze',
  },
  {
    eyebrow: 'Forecast',
    title: "Know what's coming, not just what happened.",
    body: 'Bills, subscriptions, and spending patterns are projected forward, so you can see next month before it starts.',
    illustration: 'forecast',
    reverse: true,
  },
  {
    eyebrow: 'Advise',
    title: 'Advice you can act on, not just charts.',
    body: 'FinPilot turns the forecast into a specific next move: move money, trim a category, or adjust a budget.',
    illustration: 'advise',
  },
]

export const savingsGoalPct = 70

// ---- How it works ----

export interface HowItWorksStep {
  number: number
  title: string
  body: string
}

export const howItWorksSteps: HowItWorksStep[] = [
  { number: 1, title: 'Upload or scan', body: 'Drop a bank statement CSV, or scan a UPI payment screenshot straight from your phone.' },
  { number: 2, title: 'FinPilot reads and categorizes', body: 'Every transaction is extracted, categorized, and checked for anything unusual — no manual tagging.' },
  { number: 3, title: 'Get a forecast and a next move', body: 'See what next month costs before it starts, and one specific action to act on today.' },
]

// ---- Scan a screenshot band ----

export const scanExample = {
  app: 'GPay',
  status: 'Payment successful',
  amountMinor: 45_000, // ₹450
  merchant: 'Swiggy',
  dateLabel: '9 Aug, 8:45 pm',
  reference: 'UPI Ref No 234567891023',
}

export const scanExtractedFields = [
  { label: 'Amount', value: '₹450.00' },
  { label: 'Merchant', value: 'Swiggy' },
  { label: 'Date', value: '9 Aug 2026' },
  { label: 'Category', value: 'Food' },
]

// ---- Stay safe (ported from design/FinPilot Scam Awareness.dc.html) ----
// The reference's report-fraud contact was US-specific (FTC); swapped for
// India's national cyber-crime helpline/portal so the claim is actually
// true for this app's audience.

export interface StaySafeCard {
  title: string
  desc: string
}

export const staySafeCards: StaySafeCard[] = [
  { title: 'Never share your OTP', desc: 'FinPilot support will never ask you to read out or forward a one-time passcode.' },
  { title: 'Never share your password', desc: "We'll never call, text, or email asking you to confirm your login or password." },
  { title: 'Never act on urgency', desc: 'Scammers create urgency. FinPilot never demands you move money immediately.' },
  { title: 'Never trust unknown links', desc: "We'll never send an unsolicited link asking you to log in or verify your account." },
]

export const reportFraud = {
  phone: '1930',
  portal: 'cybercrime.gov.in',
  portalUrl: 'https://cybercrime.gov.in',
}

// ---- Privacy strip ----

export const privacyClaims = [
  'We never connect to a bank account and can never move money',
  'We only read transaction data — never Gmail, Drive, or anything else in your Google account',
  'Screenshots are read and discarded, never stored',
]
