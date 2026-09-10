import statistics
from dataclasses import dataclass

from app.analysis.monthly import monthly_category_breakdown
from app.analysis.types import TxnRecord

# Z-score threshold beyond which a value is flagged. 2.0 is looser than the
# usual 3.0 "textbook outlier" cutoff — with a handful of months of demo data
# there often aren't enough points for 3-sigma events to ever fire, and a
# capstone demo needs the anomaly panel to actually show something.
Z_SCORE_THRESHOLD = 2.0
MIN_SAMPLES_FOR_STATS = 3


@dataclass(frozen=True)
class TransactionAnomaly:
    date: str
    category: str
    amount_minor: int
    z_score: float


@dataclass(frozen=True)
class CategoryMonthAnomaly:
    month: str
    category: str
    spend_minor: int
    z_score: float


def _z_scores(values: list[float]) -> list[float]:
    if len(values) < MIN_SAMPLES_FOR_STATS:
        return [0.0] * len(values)
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return [0.0] * len(values)
    return [(v - mean) / stdev for v in values]


def detect_transaction_anomalies(records: list[TxnRecord]) -> list[TransactionAnomaly]:
    """Flags individual spend transactions that are statistical outliers
    within their own category (so a one-off large rent payment doesn't get
    compared against ten-dollar coffee purchases)."""
    by_category: dict[str, list[TxnRecord]] = {}
    for r in records:
        if r.amount_minor < 0:
            by_category.setdefault(r.category, []).append(r)

    anomalies: list[TransactionAnomaly] = []
    for category, txns in by_category.items():
        amounts = [-t.amount_minor for t in txns]
        scores = _z_scores([float(a) for a in amounts])
        for txn, score in zip(txns, scores):
            if abs(score) >= Z_SCORE_THRESHOLD:
                anomalies.append(TransactionAnomaly(txn.date.isoformat(), category, txn.amount_minor, round(score, 2)))

    return sorted(anomalies, key=lambda a: -abs(a.z_score))


def detect_category_month_anomalies(records: list[TxnRecord]) -> list[CategoryMonthAnomaly]:
    """Flags category-months (e.g. "Dining, March") that are outliers versus
    that category's own history across all months."""
    by_month_category = monthly_category_breakdown(records)

    per_category_series: dict[str, list[tuple[str, int]]] = {}
    for month, cats in by_month_category.items():
        for category, spend in cats.items():
            per_category_series.setdefault(category, []).append((month, spend))

    anomalies: list[CategoryMonthAnomaly] = []
    for category, series in per_category_series.items():
        amounts = [float(spend) for _, spend in series]
        scores = _z_scores(amounts)
        for (month, spend), score in zip(series, scores):
            if abs(score) >= Z_SCORE_THRESHOLD:
                anomalies.append(CategoryMonthAnomaly(month, category, spend, round(score, 2)))

    return sorted(anomalies, key=lambda a: -abs(a.z_score))
