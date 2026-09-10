"""Summary compiler for POST /api/advice — separate from ai/summary.py
(used by the older /ai/recommendations) so that feature keeps running
completely unchanged. Reuses the same underlying analysis helpers, adds
the user's stated goals and the deterministic financial health score
(app/health/score.py) so advice can reference both without recomputing
or contradicting them."""
import hashlib
import json

from sqlalchemy.orm import Session

from app.analysis.anomalies import detect_category_month_anomalies, detect_transaction_anomalies
from app.analysis.budgets import budget_adherence
from app.analysis.monthly import category_breakdown
from app.analysis.savings import monthly_savings_rate
from app.analysis.trends import detect_trends
from app.analysis.types import TxnRecord
from app.forecasting.generate import load_records
from app.forecasting.series import total_monthly_series
from app.forecasting.service import forecast_series
from app.health.score import compute_health_score
from app.models.budget import Budget
from app.models.category import Category
from app.models.goal import Goal
from app.models.user_profile import UserProfile


def _money(minor: int) -> float:
    return round(minor / 100, 2)


def build_advice_summary(db: Session, user_id: str) -> dict:
    records: list[TxnRecord] = load_records(db, user_id)

    trends = detect_trends(records)
    txn_anomalies = detect_transaction_anomalies(records)[:10]
    month_anomalies = detect_category_month_anomalies(records)[:10]
    savings = monthly_savings_rate(records)

    budget_rows = (
        db.query(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .filter(Budget.user_id == user_id)
        .all()
    )
    budgets_minor = {cat.name: b.monthly_limit_minor for b, cat in budget_rows}
    adherence = budget_adherence(records, budgets_minor)

    total_series = total_monthly_series(records)
    total_forecast = forecast_series(total_series)

    latest_month = total_series[-1][0] if total_series else None
    latest_breakdown = category_breakdown(records, month=latest_month) if latest_month else {}

    balance_minor = sum(r.amount_minor for r in records)
    health = compute_health_score(records, balance_minor)

    goals = db.query(Goal).filter(Goal.user_id == user_id).all()

    summary = {
        "currency_note": "all amounts below are in major currency units (e.g. rupees), not minor units",
        "latest_month": latest_month,
        "latest_month_category_spend": {k: _money(v) for k, v in latest_breakdown.items()},
        "trends": [
            {
                "category": t.category,
                "latest_spend": _money(t.latest_spend_minor),
                "rolling_3mo_avg": _money(round(t.rolling_avg_minor)),
                "pct_change": None if t.pct_change is None or t.pct_change == float("inf") else round(t.pct_change, 1),
                "direction": t.direction,
            }
            for t in trends
        ],
        "transaction_anomalies": [
            {"date": a.date, "category": a.category, "amount": _money(a.amount_minor), "z_score": a.z_score}
            for a in txn_anomalies
        ],
        "category_month_anomalies": [
            {"month": a.month, "category": a.category, "spend": _money(a.spend_minor), "z_score": a.z_score}
            for a in month_anomalies
        ],
        "savings_rate_by_month": [
            {
                "month": s.month,
                "income": _money(s.income_minor),
                "spend": _money(s.spend_minor),
                "net": _money(s.net_minor),
                "savings_rate_pct": s.savings_rate_pct,
            }
            for s in savings
        ],
        "budget_adherence": [
            {
                "category": b.category,
                "limit": _money(b.limit_minor),
                "spent": _money(b.spent_minor),
                "pct_used": b.pct_used,
                "is_over": b.is_over,
            }
            for b in adherence
        ],
        "next_month_forecast": {
            "predicted_total": _money(total_forecast.predicted_minor),
            "low": _money(total_forecast.low_minor),
            "high": _money(total_forecast.high_minor),
            "model": total_forecast.model_used,
            "is_low_confidence": total_forecast.is_low_confidence,
        },
        "goals": [
            {
                "name": g.name,
                "target_amount": _money(g.target_amount_minor),
                "saved_amount": _money(g.saved_amount_minor),
                "target_date": g.target_date.isoformat(),
                "progress_pct": round(g.saved_amount_minor / g.target_amount_minor * 100, 1) if g.target_amount_minor else 0.0,
            }
            for g in goals
        ],
        # The deterministic score from app/health/score.py — the model must echo
        # this exact number as `health_score` in its output, never compute its own.
        "deterministic_health_score": {
            "score": health.score,
            "band": health.band,
            "is_provisional": health.is_provisional,
        },
        "user_profile": _profile_block(db, user_id),
    }
    return summary


def _profile_block(db: Session, user_id: str) -> dict:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None or profile.status not in ("completed", "skipped"):
        return {"risk_band": "moderate", "literacy_level": "beginner", "life_stage": None}
    return {
        "risk_band": profile.risk_band,
        "literacy_level": profile.literacy_level,
        "life_stage": profile.life_stage,
    }


def advice_data_version(summary: dict) -> str:
    # Excludes next_month_forecast: Prophet's fit isn't perfectly
    # deterministic run-to-run (confirmed — the same input series can
    # yield a 1-paisa difference in predicted/low/high across separate
    # calls), so including it here would defeat caching almost entirely.
    # Every other field is derived by pure arithmetic directly from stored
    # rows and is exactly reproducible.
    stable = {k: v for k, v in summary.items() if k != "next_month_forecast"}
    encoded = json.dumps(stable, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
