from datetime import date, datetime

from pydantic import BaseModel


class GoalResponse(BaseModel):
    id: str
    name: str
    target_amount_minor: int
    target_date: date
    saved_amount_minor: int
    created_at: datetime
    progress_pct: float
    projected_completion_date: date | None

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    name: str
    target_amount_minor: int
    target_date: date
    saved_amount_minor: int = 0


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount_minor: int | None = None
    target_date: date | None = None
    saved_amount_minor: int | None = None
