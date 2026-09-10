from datetime import date, datetime

from pydantic import BaseModel


class ForecastResponse(BaseModel):
    id: str
    generated_at: datetime
    horizon_month: date
    predicted_total_minor: int
    confidence_low_minor: int
    confidence_high_minor: int
    per_category_breakdown: dict
    model_used: str
    is_low_confidence: bool
    mae: float | None
    mape: float | None
    benchmark_model: str | None
    benchmark_mae: float | None
    benchmark_mape: float | None

    model_config = {"from_attributes": True}


class ForecastMonthPoint(BaseModel):
    month: str  # "YYYY-MM"
    predicted_minor: int
    low_minor: int
    high_minor: int


class CategoryDriver(BaseModel):
    category: str
    current_month_minor: int
    predicted_next_month_minor: int
    delta_minor: int  # predicted - current; sign shows direction


class ForecastAccuracy(BaseModel):
    month: str  # the completed month being checked
    predicted_minor: int
    actual_minor: int
    error_minor: int
    error_pct: float | None


class HorizonForecastResponse(BaseModel):
    months: list[ForecastMonthPoint]
    model_used: str
    is_low_confidence: bool
    history_months: int
    category_drivers: list[CategoryDriver]
    accuracy: ForecastAccuracy | None
