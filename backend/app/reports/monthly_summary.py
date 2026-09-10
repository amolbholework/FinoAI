from app.analysis.monthly import category_breakdown, monthly_spend_totals
from app.analysis.savings import monthly_savings_rate
from app.analysis.types import TxnRecord


def build_monthly_summary(records: list[TxnRecord], month: str) -> dict:
    spend_by_month = monthly_spend_totals(records)
    breakdown = category_breakdown(records, month=month)
    savings = {s.month: s for s in monthly_savings_rate(records)}
    savings_row = savings.get(month)

    return {
        "month": month,
        "total_spend_minor": spend_by_month.get(month, 0),
        "category_breakdown_minor": breakdown,
        "income_minor": savings_row.income_minor if savings_row else 0,
        "net_minor": savings_row.net_minor if savings_row else 0,
        "savings_rate_pct": savings_row.savings_rate_pct if savings_row else 0.0,
    }
