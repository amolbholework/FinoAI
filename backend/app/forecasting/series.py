from datetime import date

from app.analysis.monthly import monthly_category_breakdown, monthly_spend_totals
from app.analysis.types import TxnRecord


def total_monthly_series(records: list[TxnRecord]) -> list[tuple[str, int]]:
    """[("YYYY-MM", spend_minor), ...] sorted ascending, spend-only (positive)."""
    return sorted(monthly_spend_totals(records).items())


def category_monthly_series(records: list[TxnRecord], category: str) -> list[tuple[str, int]]:
    by_month = monthly_category_breakdown(records)
    return sorted((month, cats.get(category, 0)) for month, cats in by_month.items())


def next_month_str(last_month: str) -> str:
    year, month = (int(x) for x in last_month.split("-"))
    if month == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month + 1:02d}"


def month_str_to_date(month: str) -> date:
    year, month_num = (int(x) for x in month.split("-"))
    return date(year, month_num, 1)
