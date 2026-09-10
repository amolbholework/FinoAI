"""Builds the structured context object passed to Fino on every call —
recent spending by category, monthly trend, forecast, active goals, and the
onboarding-derived profile (risk band, literacy level, life stage). Reuses
ai/summary.py's build_summary for the numbers side (same pure functions the
advice panel already uses, so the two surfaces never disagree about the
user's own data) and adds goals, which the advice panel doesn't need."""

from sqlalchemy.orm import Session

from app.ai.summary import _money, build_summary
from app.analysis.goals import progress_pct
from app.models.goal import Goal


def build_fino_context(db: Session, user_id: str) -> dict:
    summary = build_summary(db, user_id)

    goals = db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.target_date).all()
    summary["active_goals"] = [
        {
            "name": g.name,
            "target_amount": _money(g.target_amount_minor),
            "saved_amount": _money(g.saved_amount_minor),
            "target_date": g.target_date.isoformat(),
            "progress_pct": progress_pct(g.target_amount_minor, g.saved_amount_minor),
        }
        for g in goals
    ]

    return summary
