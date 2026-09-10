# Financial Health Score

The health score is **computed deterministically in Python**
(`backend/app/health/score.py`), not by the AI. The same transaction data
always produces the same score. The AI advisor may *explain* the score in
plain language, but it never computes or adjusts it.

## The five pillars

Each pillar is scored 0–100 from the user's own transaction data, then
combined into a single 0–100 score using the weights below. If a pillar
can't be computed (e.g. no income has ever been recorded), it's dropped
and the remaining pillars' weights are re-normalized to still sum to 1.00
— the score is never padded with a fabricated pillar value.

| Pillar | Weight | What it measures | Formula |
|---|---|---|---|
| Savings rate | 25% | `(income − expenses) / income`, averaged over up to the last 3 months | `score = clamp(50 + avg_savings_rate_pct × 2, 0, 100)` — 0% savings rate scores 50; every 1 point of savings rate is worth 2 score points |
| Expense stability | 15% | Month-over-month volatility of total spend, over up to the last 6 months | `score = clamp(100 − coefficient_of_variation_pct, 0, 100)`, where CV = stdev / mean of monthly totals |
| Essential vs. discretionary | 20% | Share of spend (last up to 3 months) going to essential categories (Rent, Utilities, Food, Transport, Health) vs. everything else | `score = 100` if essential share ≤ 50%, else `clamp(100 − (essential_pct − 50) × 2, 0, 100)` |
| Fixed commitment load | 20% | Rent + Utilities as a share of income, last up to 3 months | `score = 100` if ≤ 30% of income, else `clamp(100 − (pct − 30) × 2.5, 0, 100)` (reaches 0 at 70% of income) |
| Buffer | 20% | Months of average recent expenses covered by the current all-time net balance | `score = clamp(months_covered / 6 × 100, 0, 100)` — 6+ months covered scores 100 |

**Overall score** = weighted average of the computable pillars' scores,
rounded to the nearest integer.

## Bands

| Score range | Band |
|---|---|
| 0–39 | Needs attention |
| 40–59 | Getting there |
| 60–79 | Stable |
| 80–100 | Strong |

## Provisional scores

A score is marked **provisional** when:
- fewer than 3 months of transaction history exist, or
- any one of the five pillars could not be computed (shown to the user as
  "couldn't be computed" rather than silently omitted or guessed at).

## Top levers

The "top 3 levers" shown alongside the score rank pillars by
`min(20, 100 − pillar_score) × pillar_weight` — a capped, weight-scaled
estimate of how many overall points a realistic improvement in that one
pillar would add. This is a heuristic for *prioritization*, not a
prediction; it deliberately caps the assumed improvement at 20 sub-score
points so a pillar already near 100 doesn't get overstated.

## Why these categories and thresholds

- **Essential categories** (Rent, Utilities, Food, Transport, Health) are
  the categories that exist regardless of discretionary choice.
  **Fixed-commitment categories** (Rent, Utilities) are the subset of
  those that don't meaningfully vary month to month — Food and Transport
  are necessary but still somewhat elastic.
- The 50%/70%/6-month/30%/70% breakpoints are round numbers chosen to
  match common personal-finance rules of thumb (the 50/30/20 budget
  split, a 3–6 month emergency fund) rather than fitted to any dataset —
  they are meant to be legible and defensible, not statistically optimal.
- Changing any of these constants only requires updating
  `backend/app/health/score.py`; this document must be kept in sync with
  it.
