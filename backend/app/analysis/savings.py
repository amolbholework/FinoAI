from dataclasses import dataclass

from app.analysis.types import TxnRecord


@dataclass(frozen=True)
class SavingsRate:
    month: str
    income_minor: int
    spend_minor: int
    net_minor: int
    savings_rate_pct: float  # net / income * 100; 0 if no income


def monthly_savings_rate(records: list[TxnRecord]) -> list[SavingsRate]:
    by_month: dict[str, dict[str, int]] = {}
    for r in records:
        key = f"{r.date.year:04d}-{r.date.month:02d}"
        bucket = by_month.setdefault(key, {"income": 0, "spend": 0})
        if r.amount_minor >= 0:
            bucket["income"] += r.amount_minor
        else:
            bucket["spend"] += -r.amount_minor

    results = []
    for month in sorted(by_month.keys()):
        income = by_month[month]["income"]
        spend = by_month[month]["spend"]
        net = income - spend
        rate = (net / income * 100) if income > 0 else 0.0
        results.append(SavingsRate(month, income, spend, net, round(rate, 1)))

    return results
