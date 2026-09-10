from datetime import date

from app.analysis.dashboard import (
    daily_burn_series,
    projected_month_end_spend,
    remaining_budget,
    spend_to_date_comparison,
    top_categories,
)
from app.analysis.types import TxnRecord


def txn(y, m, d, amount_minor, category):
    return TxnRecord(date=date(y, m, d), amount_minor=amount_minor, category=category)


def test_spend_to_date_compares_same_day_of_month():
    records = [
        txn(2026, 7, 5, -1000, "Food"),
        txn(2026, 7, 20, -9000, "Food"),  # after cutoff day, must not count
        txn(2026, 8, 5, -1500, "Food"),
    ]
    result = spend_to_date_comparison(records, as_of=date(2026, 8, 10))
    assert result.current_month == "2026-08"
    assert result.prior_month == "2026-07"
    assert result.spend_to_date_minor == 1500
    assert result.prior_spend_to_same_day_minor == 1000
    assert result.pct_change == 50.0


def test_spend_to_date_handles_zero_prior_spend():
    records = [txn(2026, 8, 5, -1500, "Food")]
    result = spend_to_date_comparison(records, as_of=date(2026, 8, 10))
    assert result.prior_spend_to_same_day_minor == 0
    assert result.pct_change == float("inf")


def test_daily_burn_series_is_cumulative_and_stops_at_as_of():
    records = [
        txn(2026, 8, 1, -100, "Food"),
        txn(2026, 8, 3, -200, "Food"),
        txn(2026, 8, 10, -9999, "Food"),  # after as_of, excluded
    ]
    points = daily_burn_series(records, as_of=date(2026, 8, 3))
    assert [p.day for p in points] == [1, 2, 3]
    assert [p.cumulative_spend_minor for p in points] == [100, 100, 300]


def test_projected_month_end_spend_extrapolates_daily_average():
    records = [txn(2026, 8, d, -100, "Food") for d in range(1, 6)]  # 500 over 5 days
    projected = projected_month_end_spend(records, as_of=date(2026, 8, 5))
    assert projected == round(100 * 31)


def test_top_categories_collapses_rest_into_other():
    records = [
        txn(2026, 8, 1, -5000, "Rent"),
        txn(2026, 8, 1, -3000, "Food"),
        txn(2026, 8, 1, -1000, "Transport"),
        txn(2026, 8, 1, -500, "Entertainment"),
        txn(2026, 8, 1, -200, "Misc"),
    ]
    slices = top_categories(records, top_n=3)
    assert [s.category for s in slices] == ["Rent", "Food", "Transport", "Other"]
    assert slices[-1].spend_minor == 700


def test_top_categories_empty_when_no_spend():
    assert top_categories([]) == []


def test_remaining_budget_sums_across_categories():
    records = [
        txn(2026, 8, 1, -4000, "Food"),
        txn(2026, 8, 1, -6000, "Transport"),
    ]
    budgets = {"Food": 5000, "Transport": 5000}
    result = remaining_budget(records, budgets, month="2026-08")
    assert result.total_limit_minor == 10000
    assert result.total_spent_minor == 10000
    assert result.remaining_minor == 0
    assert result.is_over is False
