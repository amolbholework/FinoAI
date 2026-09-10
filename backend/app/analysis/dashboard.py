"""Dashboard-specific aggregations — day-aligned month-over-month comparison,
the daily cumulative burn-rate series (powers the BurnRateStrip signature
element), top-category grouping, and a month-end spend projection. Built on
top of the same TxnRecord shape and category_breakdown()/budget_adherence()
used everywhere else, not a parallel data path."""

import calendar
from dataclasses import dataclass
from datetime import date

from app.analysis.budgets import budget_adherence
from app.analysis.monthly import category_breakdown
from app.analysis.types import TxnRecord


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _add_month(d: date, delta: int) -> date:
    month_index = d.month - 1 + delta
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


@dataclass(frozen=True)
class SpendToDate:
    current_month: str
    days_elapsed: int
    spend_to_date_minor: int
    prior_month: str
    prior_spend_to_same_day_minor: int
    pct_change: float | None  # None if there's nothing to compare against last month


def spend_to_date_comparison(records: list[TxnRecord], as_of: date) -> SpendToDate:
    """Spend so far this month vs. spend through the same day-of-month last
    month — a fair pace comparison rather than comparing a partial month to
    a complete one."""
    current_month = _month_key(as_of)
    days_elapsed = as_of.day
    prior_month = _month_key(_add_month(date(as_of.year, as_of.month, 1), -1))

    current_spend = sum(
        -r.amount_minor
        for r in records
        if r.amount_minor < 0 and _month_key(r.date) == current_month and r.date.day <= days_elapsed
    )
    prior_spend = sum(
        -r.amount_minor
        for r in records
        if r.amount_minor < 0 and _month_key(r.date) == prior_month and r.date.day <= days_elapsed
    )

    if prior_spend == 0:
        pct_change = None if current_spend == 0 else float("inf")
    else:
        pct_change = (current_spend - prior_spend) / prior_spend * 100

    return SpendToDate(current_month, days_elapsed, current_spend, prior_month, prior_spend, pct_change)


@dataclass(frozen=True)
class DailyBurnPoint:
    day: int
    cumulative_spend_minor: int


def daily_burn_series(records: list[TxnRecord], as_of: date) -> list[DailyBurnPoint]:
    """Cumulative spend for each day of the month containing `as_of`, from
    day 1 through as_of.day. Powers the BurnRateStrip sparkline."""
    current_month = _month_key(as_of)
    daily_totals = {day: 0 for day in range(1, as_of.day + 1)}
    for r in records:
        if r.amount_minor >= 0 or _month_key(r.date) != current_month or r.date.day > as_of.day:
            continue
        daily_totals[r.date.day] += -r.amount_minor

    points = []
    running = 0
    for day in range(1, as_of.day + 1):
        running += daily_totals[day]
        points.append(DailyBurnPoint(day, running))
    return points


def projected_month_end_spend(records: list[TxnRecord], as_of: date) -> int:
    """Naive linear projection: today's daily average spend rate extrapolated
    across the full month. Deliberately simple — this feeds a "you're on
    track" style read, not the forecast page's model-backed prediction."""
    burn = daily_burn_series(records, as_of)
    if not burn or as_of.day == 0:
        return 0
    spend_to_date = burn[-1].cumulative_spend_minor
    days_in_month = calendar.monthrange(as_of.year, as_of.month)[1]
    daily_avg = spend_to_date / as_of.day
    return round(daily_avg * days_in_month)


@dataclass(frozen=True)
class CategorySlice:
    category: str
    spend_minor: int
    pct_of_total: float


def top_categories(records: list[TxnRecord], month: str | None = None, top_n: int = 3) -> list[CategorySlice]:
    """The top `top_n` categories by spend for `month` (defaults to latest),
    with everything else collapsed into a single "Other" slice."""
    breakdown = category_breakdown(records, month=month)  # already sorted desc by spend
    total = sum(breakdown.values())
    if total == 0:
        return []

    items = list(breakdown.items())
    top, rest = items[:top_n], items[top_n:]

    slices = [CategorySlice(cat, spend, round(spend / total * 100, 1)) for cat, spend in top]
    other_spend = sum(spend for _, spend in rest)
    if other_spend > 0:
        slices.append(CategorySlice("Other", other_spend, round(other_spend / total * 100, 1)))
    return slices


@dataclass(frozen=True)
class RemainingBudget:
    total_limit_minor: int
    total_spent_minor: int
    remaining_minor: int
    pct_used: float
    is_over: bool


def remaining_budget(
    records: list[TxnRecord], budgets_minor: dict[str, int], month: str | None = None
) -> RemainingBudget:
    """Sums budget_adherence() across all budgeted categories into one
    dashboard-level "how much room is left this month" figure."""
    rows = budget_adherence(records, budgets_minor, month=month)
    total_limit = sum(r.limit_minor for r in rows)
    total_spent = sum(r.spent_minor for r in rows)
    pct_used = round(total_spent / total_limit * 100, 1) if total_limit > 0 else 0.0
    return RemainingBudget(total_limit, total_spent, total_limit - total_spent, pct_used, total_spent > total_limit)
