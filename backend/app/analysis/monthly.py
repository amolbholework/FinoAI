from collections import defaultdict

from app.analysis.types import TxnRecord


def _month_key(d) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def monthly_totals(records: list[TxnRecord]) -> dict[str, int]:
    """{"YYYY-MM": net_amount_minor} across all categories, spend and income combined."""
    totals: dict[str, int] = defaultdict(int)
    for r in records:
        totals[_month_key(r.date)] += r.amount_minor
    return dict(sorted(totals.items()))


def monthly_spend_totals(records: list[TxnRecord]) -> dict[str, int]:
    """Absolute spend only (excludes income), positive numbers."""
    totals: dict[str, int] = defaultdict(int)
    for r in records:
        if r.amount_minor < 0:
            totals[_month_key(r.date)] += -r.amount_minor
    return dict(sorted(totals.items()))


def category_breakdown(records: list[TxnRecord], month: str | None = None) -> dict[str, int]:
    """Spend per category (positive minor units), optionally filtered to one "YYYY-MM"."""
    totals: dict[str, int] = defaultdict(int)
    for r in records:
        if r.amount_minor >= 0:
            continue
        if month and _month_key(r.date) != month:
            continue
        totals[r.category] += -r.amount_minor
    return dict(sorted(totals.items(), key=lambda kv: -kv[1]))


def monthly_category_breakdown(records: list[TxnRecord]) -> dict[str, dict[str, int]]:
    """{"YYYY-MM": {category: spend_minor}}."""
    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in records:
        if r.amount_minor >= 0:
            continue
        result[_month_key(r.date)][r.category] += -r.amount_minor
    return {m: dict(cats) for m, cats in sorted(result.items())}
