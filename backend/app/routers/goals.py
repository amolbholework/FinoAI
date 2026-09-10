from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analysis.goals import progress_pct, project_completion_date
from app.analysis.savings import monthly_savings_rate
from app.core.database import get_db
from app.core.security import get_effective_user
from app.forecasting.generate import load_records
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"])


def _avg_monthly_net(db: Session, user_id: str) -> float:
    rates = monthly_savings_rate(load_records(db, user_id))
    recent = rates[-3:] if len(rates) > 3 else rates
    if not recent:
        return 0.0
    return sum(r.net_minor for r in recent) / len(recent)


def _to_response(goal: Goal, avg_monthly_net: float) -> GoalResponse:
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        target_amount_minor=goal.target_amount_minor,
        target_date=goal.target_date,
        saved_amount_minor=goal.saved_amount_minor,
        created_at=goal.created_at,
        progress_pct=progress_pct(goal.target_amount_minor, goal.saved_amount_minor),
        projected_completion_date=project_completion_date(
            goal.target_amount_minor, goal.saved_amount_minor, avg_monthly_net, date.today()
        ),
    )


@router.get("", response_model=list[GoalResponse])
def list_goals(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    avg_net = _avg_monthly_net(db, current_user.id)
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).order_by(Goal.target_date).all()
    return [_to_response(g, avg_net) for g in goals]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    goal = Goal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _to_response(goal, _avg_monthly_net(db, current_user.id))


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return _to_response(goal, _avg_monthly_net(db, current_user.id))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found.")
    db.delete(goal)
    db.commit()
