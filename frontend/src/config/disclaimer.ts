// Single source of truth for the regulatory disclaimer copy — every
// surface that shows disclaimer text (the persistent bar, the fund
// screener, Fino Buddy) reads from here so it's edited in exactly one
// place. Do not paraphrase this elsewhere in the app.

export const DISCLAIMER_FULL =
  'FinPilot AI is an educational and personal-finance planning tool. It is not a SEBI-registered ' +
  'investment adviser or mutual fund distributor. Nothing here is investment advice or a ' +
  'recommendation to buy or sell any security. Mutual fund investments are subject to market risks — ' +
  'read all scheme-related documents carefully. Past performance does not indicate future returns. ' +
  'Consult a SEBI-registered adviser before investing.'

export const DISCLAIMER_CONDENSED =
  'Educational tool, not investment advice. Not a SEBI-registered adviser. Mutual funds are subject ' +
  'to market risks.'

// Routes where the full text should always show rather than the condensed
// line + expander — anywhere fund data, fund guidance, or AI-generated
// financial advice is on screen.
export const DISCLAIMER_FULL_ROUTE_PREFIXES = ['/funds', '/fino/buddy', '/advice']
