from dataclasses import dataclass

from app.analysis.monthly import category_breakdown
from app.analysis.types import TxnRecord


@dataclass(frozen=True)
class BudgetAdherence:
    category: str
    limit_minor: int
    spent_minor: int
    pct_used: float
    is_over: bool


def budget_adherence(
    records: list[TxnRecord], budgets_minor: dict[str, int], month: str | None = None
) -> list[BudgetAdherence]:
    """budgets_minor: {category_name: monthly_limit_minor}. Compares each
    budgeted category's actual spend for `month` (defaults to the latest
    month present in the data) against its limit."""
    if month is None:
        months = sorted({f"{r.date.year:04d}-{r.date.month:02d}" for r in records})
        month = months[-1] if months else None

    spend = category_breakdown(records, month=month) if month else {}

    results = []
    for category, limit in budgets_minor.items():
        spent = spend.get(category, 0)
        pct_used = (spent / limit * 100) if limit > 0 else 0.0
        results.append(BudgetAdherence(category, limit, spent, round(pct_used, 1), spent > limit))

    return sorted(results, key=lambda b: -b.pct_used)
