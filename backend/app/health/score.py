"""Deterministic financial health scoring — pure Python, no AI. Same inputs
always give the same score, so it's fully documented and defensible (see
docs/health-score.md, which must be kept in sync with the constants below).

Reads only from the same TxnRecord shape and analysis helpers everything
else in app/analysis/ uses — this module doesn't touch the database itself,
so it's trivially unit-testable and the health-checker feature can be
disabled without touching any of this code."""

import statistics
from dataclasses import dataclass

from app.analysis.monthly import category_breakdown, monthly_spend_totals
from app.analysis.savings import SavingsRate, monthly_savings_rate
from app.analysis.types import TxnRecord

# Weights sum to 1.00 — see docs/health-score.md for the rationale behind
# each. If a pillar can't be computed (e.g. no income recorded), the
# remaining pillars' weights are re-normalized to still sum to 1.00.
WEIGHT_SAVINGS_RATE = 0.25
WEIGHT_EXPENSE_STABILITY = 0.15
WEIGHT_ESSENTIAL_DISCRETIONARY = 0.20
WEIGHT_FIXED_COMMITMENT = 0.20
WEIGHT_BUFFER = 0.20

# "Needs" categories for the essential-vs-discretionary and fixed-commitment
# pillars. Fixed commitment is a subset of essential — Food and Transport
# vary month to month even though they're necessary, Rent and Utilities
# don't (or barely do).
ESSENTIAL_CATEGORIES = {"Rent", "Utilities", "Food", "Transport", "Health"}
FIXED_COMMITMENT_CATEGORIES = {"Rent", "Utilities"}

# Band thresholds — score is 0-100 inclusive.
BAND_THRESHOLDS: list[tuple[int, int, str]] = [
    (0, 40, "Needs attention"),
    (40, 60, "Getting there"),
    (60, 80, "Stable"),
    (80, 101, "Strong"),
]

LOOKBACK_MONTHS = 3  # pillars average over up to this many recent months
STABILITY_LOOKBACK_MONTHS = 6
TARGET_BUFFER_MONTHS = 6  # months of expenses covered -> full buffer score
LEVER_STEP_POINTS = 20  # "what would move it" assumes this much sub-score headroom


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def band_for_score(score: float) -> str:
    for low, high, label in BAND_THRESHOLDS:
        if low <= score < high:
            return label
    return BAND_THRESHOLDS[-1][2]


@dataclass(frozen=True)
class Pillar:
    key: str
    label: str
    score: float | None  # 0-100, or None if not computable from this user's data
    weight: float
    value_label: str  # the real figure behind the score, e.g. "18% savings rate"
    note: str  # one line: what's driving it, or what would move it


@dataclass(frozen=True)
class HealthScoreResult:
    score: int | None  # None only when literally nothing was computable
    band: str | None
    is_provisional: bool  # under 3 months of history, or any pillar missing
    pillars: list[Pillar]


def _savings_rate_pillar(rates: list[SavingsRate]) -> Pillar:
    recent = [r for r in rates[-LOOKBACK_MONTHS:] if r.income_minor > 0]
    if not recent:
        return Pillar(
            "savings_rate", "Savings rate", None, WEIGHT_SAVINGS_RATE,
            "no income recorded", "Log income transactions so this can be computed.",
        )
    avg_rate = sum(r.savings_rate_pct for r in recent) / len(recent)
    # 0% savings rate -> 50; every 1 point of savings rate is worth 2 score points.
    score = _clamp(50 + avg_rate * 2, 0, 100)
    note = (
        "Keep it up — you're saving a healthy share of income."
        if avg_rate >= 20
        else "Saving a larger share of income each month would raise this."
    )
    return Pillar(
        "savings_rate", "Savings rate", round(score, 1), WEIGHT_SAVINGS_RATE,
        f"{avg_rate:.1f}% average savings rate", note,
    )


def _expense_stability_pillar(records: list[TxnRecord]) -> Pillar:
    totals = sorted(monthly_spend_totals(records).items())[-STABILITY_LOOKBACK_MONTHS:]
    values = [v for _, v in totals]
    if len(values) < 2 or sum(values) == 0:
        return Pillar(
            "expense_stability", "Expense stability", None, WEIGHT_EXPENSE_STABILITY,
            "not enough months of history", "A few more months of spending history will let this be computed.",
        )
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    cv_pct = (stdev / mean * 100) if mean else 0.0
    score = _clamp(100 - cv_pct, 0, 100)
    note = (
        "Your spending is consistent month to month."
        if cv_pct <= 30
        else "Spend varies a lot month to month — smoothing out irregular costs (e.g. a sinking fund) would help."
    )
    return Pillar(
        "expense_stability", "Expense stability", round(score, 1), WEIGHT_EXPENSE_STABILITY,
        f"{cv_pct:.0f}% month-to-month variation", note,
    )


def _essential_discretionary_pillar(records: list[TxnRecord]) -> Pillar:
    months = sorted(monthly_spend_totals(records).keys())[-LOOKBACK_MONTHS:]
    if not months:
        return Pillar(
            "essential_discretionary", "Essential vs. discretionary", None, WEIGHT_ESSENTIAL_DISCRETIONARY,
            "no spend recorded", "Add some transactions so this can be computed.",
        )
    essential = 0
    total = 0
    for month in months:
        breakdown = category_breakdown(records, month=month)
        for category, amount in breakdown.items():
            total += amount
            if category in ESSENTIAL_CATEGORIES:
                essential += amount
    if total == 0:
        return Pillar(
            "essential_discretionary", "Essential vs. discretionary", None, WEIGHT_ESSENTIAL_DISCRETIONARY,
            "no spend recorded", "Add some transactions so this can be computed.",
        )
    essential_pct = essential / total * 100
    # <=50% essential -> full score; every point above 50 costs 2 score points.
    score = 100.0 if essential_pct <= 50 else _clamp(100 - (essential_pct - 50) * 2, 0, 100)
    note = (
        "You have healthy room between essentials and discretionary spend."
        if essential_pct <= 70
        else "A large share of spend goes to essentials, leaving little room to save — trimming discretionary "
        "categories or renegotiating a fixed cost would help."
    )
    return Pillar(
        "essential_discretionary", "Essential vs. discretionary", round(score, 1), WEIGHT_ESSENTIAL_DISCRETIONARY,
        f"{essential_pct:.0f}% of spend on essentials", note,
    )


def _fixed_commitment_pillar(records: list[TxnRecord], rates: list[SavingsRate]) -> Pillar:
    months = sorted(monthly_spend_totals(records).keys())[-LOOKBACK_MONTHS:]
    income_by_month = {r.month: r.income_minor for r in rates}
    fixed = 0
    income = 0
    for month in months:
        breakdown = category_breakdown(records, month=month)
        fixed += sum(amount for category, amount in breakdown.items() if category in FIXED_COMMITMENT_CATEGORIES)
        income += income_by_month.get(month, 0)
    if income == 0:
        return Pillar(
            "fixed_commitment", "Fixed commitment load", None, WEIGHT_FIXED_COMMITMENT,
            "no income recorded", "Log income transactions so this can be computed.",
        )
    pct = fixed / income * 100
    # <=30% of income -> full score; every point above 30 costs 2.5 score points (0 at 70%).
    score = 100.0 if pct <= 30 else _clamp(100 - (pct - 30) * 2.5, 0, 100)
    note = (
        "Fixed commitments leave healthy room in your income."
        if pct <= 50
        else "Fixed commitments take up a large share of income — refinancing or renegotiating one would free up the most room."
    )
    return Pillar(
        "fixed_commitment", "Fixed commitment load", round(score, 1), WEIGHT_FIXED_COMMITMENT,
        f"{pct:.0f}% of income on rent/utilities", note,
    )


def _buffer_pillar(records: list[TxnRecord], balance_minor: int) -> Pillar:
    totals = sorted(monthly_spend_totals(records).items())[-LOOKBACK_MONTHS:]
    values = [v for _, v in totals]
    if not values or sum(values) == 0:
        return Pillar(
            "buffer", "Buffer", None, WEIGHT_BUFFER,
            "no spend recorded", "Add some transactions so this can be computed.",
        )
    avg_monthly_expense = sum(values) / len(values)
    months_covered = balance_minor / avg_monthly_expense if avg_monthly_expense else 0.0
    score = _clamp(months_covered / TARGET_BUFFER_MONTHS * 100, 0, 100)
    note = (
        "You have a solid cushion of expenses covered."
        if months_covered >= TARGET_BUFFER_MONTHS
        else f"Building toward {TARGET_BUFFER_MONTHS} months of expenses in reserve would raise this."
    )
    return Pillar(
        "buffer", "Buffer", round(score, 1), WEIGHT_BUFFER,
        f"{months_covered:.1f} months of expenses covered", note,
    )


def compute_health_score(records: list[TxnRecord], balance_minor: int) -> HealthScoreResult:
    """balance_minor: the same all-time net balance figure the dashboard
    already computes (GET /analysis/balance) — no new store of sensitive
    judgements about the user, this is derived fresh from existing data."""
    rates = monthly_savings_rate(records)
    pillars = [
        _savings_rate_pillar(rates),
        _expense_stability_pillar(records),
        _essential_discretionary_pillar(records),
        _fixed_commitment_pillar(records, rates),
        _buffer_pillar(records, balance_minor),
    ]

    computable = [p for p in pillars if p.score is not None]
    if not computable:
        return HealthScoreResult(None, None, True, pillars)

    total_weight = sum(p.weight for p in computable)
    weighted = sum((p.score or 0) * p.weight for p in computable) / total_weight
    score = round(weighted)
    band = band_for_score(score)
    is_provisional = len(computable) < len(pillars) or len(rates) < 3

    return HealthScoreResult(score, band, is_provisional, pillars)


@dataclass(frozen=True)
class Lever:
    pillar_key: str
    pillar_label: str
    current_score: float
    estimated_point_gain: float  # on the overall 0-100 score, not the pillar's own score
    note: str


def top_levers(result: HealthScoreResult, limit: int = 3) -> list[Lever]:
    """The pillars with the most realistic headroom, ranked by how much a
    modest (LEVER_STEP_POINTS) improvement in that pillar would move the
    overall score — weight-heavy pillars with low scores rank first."""
    levers = []
    for pillar in result.pillars:
        if pillar.score is None or pillar.score >= 100:
            continue
        step = min(LEVER_STEP_POINTS, 100 - pillar.score)
        gain = step * pillar.weight
        levers.append(
            Lever(pillar.key, pillar.label, pillar.score, round(gain, 1), pillar.note)
        )
    levers.sort(key=lambda l: -l.estimated_point_gain)
    return levers[:limit]
