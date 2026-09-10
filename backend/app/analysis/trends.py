from dataclasses import dataclass

from app.analysis.monthly import monthly_category_breakdown
from app.analysis.types import TxnRecord

RISING_THRESHOLD_PCT = 15.0
FALLING_THRESHOLD_PCT = -15.0


@dataclass(frozen=True)
class CategoryTrend:
    category: str
    latest_month: str
    latest_spend_minor: int
    rolling_avg_minor: float  # average of the up-to-3 months before latest_month
    pct_change: float | None  # None if there's no prior average to compare against
    direction: str  # "rising" | "falling" | "stable"


def detect_trends(records: list[TxnRecord]) -> list[CategoryTrend]:
    """For the most recent month present in the data, compares each category's
    spend against its trailing 3-month rolling average (excluding that month)."""
    by_month = monthly_category_breakdown(records)
    months = sorted(by_month.keys())
    if not months:
        return []

    latest_month = months[-1]
    prior_months = months[-4:-1] if len(months) > 1 else []

    categories = set(by_month[latest_month].keys())
    for m in prior_months:
        categories |= set(by_month[m].keys())

    trends: list[CategoryTrend] = []
    for category in sorted(categories):
        latest_spend = by_month[latest_month].get(category, 0)
        prior_values = [by_month[m].get(category, 0) for m in prior_months]

        if not prior_values:
            trends.append(CategoryTrend(category, latest_month, latest_spend, 0.0, None, "stable"))
            continue

        rolling_avg = sum(prior_values) / len(prior_values)
        if rolling_avg == 0:
            pct_change = None if latest_spend == 0 else float("inf")
        else:
            pct_change = (latest_spend - rolling_avg) / rolling_avg * 100

        if pct_change is None:
            direction = "stable"
        elif pct_change == float("inf") or pct_change >= RISING_THRESHOLD_PCT:
            direction = "rising"
        elif pct_change <= FALLING_THRESHOLD_PCT:
            direction = "falling"
        else:
            direction = "stable"

        trends.append(CategoryTrend(category, latest_month, latest_spend, rolling_avg, pct_change, direction))

    return trends
