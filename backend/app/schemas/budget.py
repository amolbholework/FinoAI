from datetime import datetime

from pydantic import BaseModel


class BudgetResponse(BaseModel):
    id: str
    category_id: str
    category_name: str | None = None
    monthly_limit_minor: int
    period: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetUpsert(BaseModel):
    category_id: str
    monthly_limit_minor: int
