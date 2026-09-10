from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.ai.advice import get_advice
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import enforce_ip_rate_limit
from app.core.security import get_effective_user
from app.models.advice import Advice, AdviceActionState
from app.models.user import User
from app.schemas.advice import (
    AdviceApiResponse,
    AdviceHistoryItem,
    RecommendationActionIn,
    RecommendationApiOut,
)

router = APIRouter(prefix="/api/advice", tags=["advice"])

VALID_STATUSES = {"pending", "dismissed", "done"}
HISTORY_LIMIT = 10


def _recommendation_out(advice_id: str, index: int, r: dict, status: str) -> RecommendationApiOut:
    return RecommendationApiOut(
        id=f"{advice_id}:{index}",
        action=r["action"],
        why=r["why"],
        impact_inr_per_month=r["impact_inr_per_month"],
        effort=r["effort"],
        category=r["category"],
        horizon=r["horizon"],
        linked_goal=r.get("linked_goal"),
        goal_impact=r.get("goal_impact"),
        status=status,
    )


def _serialize(advice: Advice, db: Session, was_cached: bool) -> AdviceApiResponse:
    output = advice.output
    states = {
        s.recommendation_index: s.status
        for s in db.query(AdviceActionState).filter(AdviceActionState.advice_id == advice.id).all()
    }
    recommendations = [
        _recommendation_out(advice.id, i, r, states.get(i, "pending"))
        for i, r in enumerate(output.get("recommendations", []))
    ]
    return AdviceApiResponse(
        advice_id=advice.id,
        generated_at=advice.generated_at.isoformat(),
        cached=was_cached,
        is_fallback=advice.is_fallback,
        headline=output["headline"],
        health_score=output["health_score"],
        insights=output.get("insights", []),
        recommendations=recommendations,
        questions_to_consider=output.get("questions_to_consider", []),
    )


@router.post("", response_model=AdviceApiResponse)
def post_advice(
    request: Request,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    settings = get_settings()
    if current_user.is_demo:
        enforce_ip_rate_limit(request, f"advice-demo-{current_user.id}", max_per_minute=settings.ai_demo_rate_limit_per_minute)

    advice, was_cached = get_advice(db, current_user.id, force_refresh=force_refresh)
    return _serialize(advice, db, was_cached)


@router.get("/history", response_model=list[AdviceHistoryItem])
def get_advice_history(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    """A simple record of past advice generations — lets the user see how
    the headline/score changed over time, not just the current one."""
    rows = (
        db.query(Advice)
        .filter(Advice.user_id == current_user.id)
        .order_by(Advice.generated_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    return [
        AdviceHistoryItem(
            advice_id=row.id,
            generated_at=row.generated_at.isoformat(),
            headline=row.output["headline"],
            health_score=row.output["health_score"],
            is_fallback=row.is_fallback,
        )
        for row in rows
    ]


@router.patch("/recommendations/{rec_id}/status", response_model=RecommendationApiOut)
def set_recommendation_status(
    rec_id: str,
    body: RecommendationActionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    try:
        advice_id, index_str = rec_id.rsplit(":", 1)
        index = int(index_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed recommendation id")

    advice = db.query(Advice).filter(Advice.id == advice_id, Advice.user_id == current_user.id).first()
    if advice is None:
        raise HTTPException(status_code=404, detail="Advice not found")
    if index < 0 or index >= len(advice.output.get("recommendations", [])):
        raise HTTPException(status_code=404, detail="Recommendation not found")

    existing = (
        db.query(AdviceActionState)
        .filter(AdviceActionState.advice_id == advice_id, AdviceActionState.recommendation_index == index)
        .first()
    )

    if body.status == "pending":
        if existing:
            db.delete(existing)
            db.commit()
    elif existing:
        existing.status = body.status
        db.commit()
    else:
        db.add(AdviceActionState(advice_id=advice_id, recommendation_index=index, status=body.status))
        db.commit()

    r = advice.output["recommendations"][index]
    return _recommendation_out(advice_id, index, r, body.status)
