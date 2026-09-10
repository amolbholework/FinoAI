from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.monthly import monthly_spend_totals
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_effective_user
from app.forecasting.generate import load_records
from app.health.score import compute_health_score, top_levers
from app.models.user import User
from app.schemas.health import HealthLeverOut, HealthPillarOut, HealthScoreOut, HealthTrendPoint

router = APIRouter(prefix="/api/health", tags=["health"])

TREND_MONTHS = 6


@router.get("/score", response_model=HealthScoreOut)
def get_health_score(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    """Additive, feature-flagged, and reads only from the same analysis
    helpers every other endpoint uses — see docs/health-score.md for the
    scoring model and tests/test_health_endpoint.py for the proof that
    disabling health_checker_enabled changes nothing else in the app."""
    settings = get_settings()
    if not settings.health_checker_enabled:
        raise HTTPException(status_code=404, detail="Not found")

    records = load_records(db, current_user.id)
    balance_minor = sum(r.amount_minor for r in records)
    result = compute_health_score(records, balance_minor)

    trend: list[HealthTrendPoint] = []
    months = sorted(monthly_spend_totals(records).keys())[-TREND_MONTHS:]
    for month in months:
        year, month_num = (int(x) for x in month.split("-"))
        cumulative = [r for r in records if (r.date.year, r.date.month) <= (year, month_num)]
        cumulative_balance = sum(r.amount_minor for r in cumulative)
        point_result = compute_health_score(cumulative, cumulative_balance)
        if point_result.score is not None:
            trend.append(HealthTrendPoint(month=month, score=point_result.score))

    return HealthScoreOut(
        score=result.score,
        band=result.band,
        is_provisional=result.is_provisional,
        pillars=[HealthPillarOut(**p.__dict__) for p in result.pillars],
        top_levers=[HealthLeverOut(**l.__dict__) for l in top_levers(result)],
        trend=trend,
    )
