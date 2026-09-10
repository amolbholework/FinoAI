from datetime import date

from app.analysis.types import TxnRecord
from app.health.score import band_for_score, compute_health_score, top_levers


def _month_records(year: int, month: int, income: int, categories: dict[str, int]) -> list[TxnRecord]:
    """income and each category value are in minor units, positive spend amounts."""
    records = [TxnRecord(date=date(year, month, 1), amount_minor=income, category="Income")]
    for category, amount in categories.items():
        records.append(TxnRecord(date=date(year, month, 15), amount_minor=-amount, category=category))
    return records


def _build_fixture(income: int, categories: dict[str, int]) -> list[TxnRecord]:
    """Three identical months (Jan-Mar 2026) — enough history to make every
    pillar computable and non-provisional, with zero month-to-month
    variation so expense stability doesn't skew the target band."""
    records: list[TxnRecord] = []
    for month in (1, 2, 3):
        records += _month_records(2026, month, income, categories)
    return records


def test_band_thresholds_are_exact():
    assert band_for_score(0) == "Needs attention"
    assert band_for_score(39) == "Needs attention"
    assert band_for_score(40) == "Getting there"
    assert band_for_score(59) == "Getting there"
    assert band_for_score(60) == "Stable"
    assert band_for_score(79) == "Stable"
    assert band_for_score(80) == "Strong"
    assert band_for_score(100) == "Strong"


def test_strong_band_fixture():
    # 30% savings rate, 50% essential share, 25% fixed-commitment share, 6mo buffer.
    records = _build_fixture(
        income=100_000,
        categories={"Rent": 20_000, "Utilities": 5_000, "Food": 6_000, "Transport": 3_000, "Health": 1_000, "Shopping": 25_000, "Entertainment": 10_000},
    )
    result = compute_health_score(records, balance_minor=420_000)
    assert result.band == "Strong"
    assert result.is_provisional is False
    assert all(p.score is not None for p in result.pillars)


def test_needs_attention_band_fixture():
    # Negative savings rate, 90% essential share, 70% fixed-commitment share, zero buffer.
    records = _build_fixture(
        income=50_000,
        categories={"Rent": 30_000, "Utilities": 5_000, "Food": 12_000, "Transport": 6_000, "Health": 1_000, "Shopping": 4_000, "Entertainment": 2_000},
    )
    result = compute_health_score(records, balance_minor=0)
    assert result.band == "Needs attention"


def test_getting_there_band_fixture():
    records = _build_fixture(
        income=60_000,
        categories={"Rent": 25_000, "Utilities": 8_000, "Food": 9_000, "Transport": 4_000, "Health": 2_000, "Shopping": 8_000, "Entertainment": 4_000},
    )
    result = compute_health_score(records, balance_minor=90_000)
    assert result.band == "Getting there"


def test_stable_band_fixture():
    records = _build_fixture(
        income=80_000,
        categories={"Rent": 25_000, "Utilities": 8_600, "Food": 8_000, "Transport": 4_000, "Health": 1_000, "Shopping": 18_000, "Entertainment": 9_000},
    )
    result = compute_health_score(records, balance_minor=250_000)
    assert result.band == "Stable"


def test_empty_records_returns_no_score():
    result = compute_health_score([], balance_minor=0)
    assert result.score is None
    assert result.band is None
    assert result.is_provisional is True
    assert all(p.score is None for p in result.pillars)


def test_no_income_marks_income_dependent_pillars_unavailable_not_fabricated():
    records = [TxnRecord(date=date(2026, 1, 15), amount_minor=-5000, category="Food")]
    result = compute_health_score(records, balance_minor=10_000)
    by_key = {p.key: p for p in result.pillars}
    assert by_key["savings_rate"].score is None
    assert by_key["fixed_commitment"].score is None
    assert result.is_provisional is True
    # Essential/discretionary and buffer don't need income, so they're still computed.
    assert by_key["essential_discretionary"].score is not None
    assert by_key["buffer"].score is not None


def test_under_three_months_history_is_provisional():
    records = _month_records(2026, 1, 50_000, {"Food": 20_000})
    result = compute_health_score(records, balance_minor=10_000)
    assert result.is_provisional is True


def test_top_levers_are_sorted_by_estimated_gain_and_capped():
    records = _build_fixture(
        income=50_000,
        categories={"Rent": 30_000, "Utilities": 5_000, "Food": 12_000, "Transport": 6_000, "Health": 1_000, "Shopping": 4_000, "Entertainment": 2_000},
    )
    result = compute_health_score(records, balance_minor=0)
    levers = top_levers(result, limit=3)
    assert len(levers) <= 3
    gains = [l.estimated_point_gain for l in levers]
    assert gains == sorted(gains, reverse=True)
    for lever in levers:
        assert lever.estimated_point_gain > 0


def test_top_levers_excludes_pillars_already_at_100():
    records = _build_fixture(
        income=100_000,
        categories={"Rent": 20_000, "Utilities": 5_000, "Food": 6_000, "Transport": 3_000, "Health": 1_000, "Shopping": 25_000, "Entertainment": 10_000},
    )
    result = compute_health_score(records, balance_minor=420_000)
    levers = top_levers(result, limit=5)
    lever_keys = {l.pillar_key for l in levers}
    perfect_keys = {p.key for p in result.pillars if p.score == 100}
    assert lever_keys.isdisjoint(perfect_keys)
