from datetime import date

from app.analysis.anomalies import detect_category_month_anomalies, detect_transaction_anomalies
from app.analysis.budgets import budget_adherence
from app.analysis.monthly import category_breakdown, monthly_spend_totals
from app.analysis.savings import monthly_savings_rate
from app.analysis.trends import detect_trends
from app.analysis.types import TxnRecord


def txn(y, m, d, amount_minor, category):
    return TxnRecord(date=date(y, m, d), amount_minor=amount_minor, category=category)


def test_monthly_spend_totals_ignores_income():
    records = [
        txn(2026, 1, 5, -1000, "Food"),
        txn(2026, 1, 10, -2000, "Transport"),
        txn(2026, 1, 15, 50000, "Income"),
        txn(2026, 2, 1, -500, "Food"),
    ]
    totals = monthly_spend_totals(records)
    assert totals == {"2026-01": 3000, "2026-02": 500}


def test_category_breakdown_filters_by_month():
    records = [
        txn(2026, 1, 5, -1000, "Food"),
        txn(2026, 2, 5, -4000, "Food"),
    ]
    assert category_breakdown(records, month="2026-01") == {"Food": 1000}
    assert category_breakdown(records, month="2026-02") == {"Food": 4000}


def test_trend_detection_flags_rising_category():
    records = []
    for month in (1, 2, 3):
        records.append(txn(2026, month, 10, -1000, "Food"))
    records.append(txn(2026, 4, 10, -2000, "Food"))  # 100% above the 3-month average

    trends = {t.category: t for t in detect_trends(records)}
    assert trends["Food"].direction == "rising"
    assert trends["Food"].pct_change == 100.0


def test_trend_detection_flags_falling_category():
    records = []
    for month in (1, 2, 3):
        records.append(txn(2026, month, 10, -2000, "Transport"))
    records.append(txn(2026, 4, 10, -500, "Transport"))  # well below average

    trends = {t.category: t for t in detect_trends(records)}
    assert trends["Transport"].direction == "falling"


def test_transaction_anomaly_flags_large_outlier():
    records = [txn(2026, 1, d, -300, "Food") for d in range(1, 10)]
    records.append(txn(2026, 1, 15, -50000, "Food"))  # way outside the norm

    anomalies = detect_transaction_anomalies(records)
    assert any(a.amount_minor == -50000 for a in anomalies)


def test_category_month_anomaly_flags_outlier_month():
    records = []
    for month in (1, 2, 3, 4, 5):
        records.append(txn(2026, month, 10, -1000, "Shopping"))
    records.append(txn(2026, 6, 10, -30000, "Shopping"))

    anomalies = detect_category_month_anomalies(records)
    assert any(a.month == "2026-06" and a.category == "Shopping" for a in anomalies)


def test_budget_adherence_flags_overspend():
    records = [txn(2026, 1, 5, -9000, "Food")]
    result = budget_adherence(records, {"Food": 8000}, month="2026-01")
    assert result[0].is_over is True
    assert result[0].pct_used == 112.5


def test_budget_adherence_under_limit():
    records = [txn(2026, 1, 5, -3000, "Food")]
    result = budget_adherence(records, {"Food": 8000}, month="2026-01")
    assert result[0].is_over is False


def test_savings_rate_computation():
    records = [
        txn(2026, 1, 1, 50000, "Income"),
        txn(2026, 1, 10, -20000, "Food"),
    ]
    rates = monthly_savings_rate(records)
    assert len(rates) == 1
    assert rates[0].income_minor == 50000
    assert rates[0].spend_minor == 20000
    assert rates[0].net_minor == 30000
    assert rates[0].savings_rate_pct == 60.0


def test_savings_rate_zero_income_does_not_divide_by_zero():
    records = [txn(2026, 1, 10, -20000, "Food")]
    rates = monthly_savings_rate(records)
    assert rates[0].savings_rate_pct == 0.0
