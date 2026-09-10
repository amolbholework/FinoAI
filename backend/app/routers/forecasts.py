from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.monthly import category_breakdown
from app.core.database import get_db
from app.core.security import get_effective_user
from app.forecasting.generate import generate_forecast, load_records
from app.forecasting.series import category_monthly_series, month_str_to_date, next_month_str, total_monthly_series
from app.forecasting.service import forecast_horizon, forecast_series
from app.models.forecast import Forecast
from app.models.user import User
from app.schemas.forecast import (
    CategoryDriver,
    ForecastAccuracy,
    ForecastMonthPoint,
    ForecastResponse,
    HorizonForecastResponse,
)

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("/latest", response_model=ForecastResponse)
def latest_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    existing = (
        db.query(Forecast)
        .filter(Forecast.user_id == current_user.id)
        .order_by(Forecast.generated_at.desc())
        .first()
    )
    if existing:
        return existing
    return generate_forecast(db, current_user.id)


@router.post("/generate", response_model=ForecastResponse)
def regenerate_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return generate_forecast(db, current_user.id)


@router.get("/horizon", response_model=HorizonForecastResponse)
def horizon_forecast(
    months: int = 1, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    """Powers the forecast page's 1/3/6-month control: a run of monthly
    points with confidence bands, the categories driving next month's
    predicted change, and — when a past forecast exists for it — how last
    month's prediction compared to what actually happened."""
    if months not in (1, 3, 6):
        raise HTTPException(status_code=400, detail="months must be 1, 3, or 6")

    records = load_records(db, current_user.id)
    total_series = total_monthly_series(records)
    history_months = len(total_series)

    points, model_used, is_low_confidence = forecast_horizon(total_series, months)

    start_month = total_series[-1][0] if total_series else "2000-01"
    month_labels = []
    cursor = start_month
    for _ in range(months):
        cursor = next_month_str(cursor)
        month_labels.append(cursor)

    month_points = [
        ForecastMonthPoint(month=m, predicted_minor=p.predicted_minor, low_minor=p.low_minor, high_minor=p.high_minor)
        for m, p in zip(month_labels, points)
    ]

    # Top movers: forecast each category one month ahead and compare to its
    # current-month actual — the categories with the largest predicted swing,
    # not just the largest predicted total.
    current_month = total_series[-1][0] if total_series else None
    current_breakdown = category_breakdown(records, month=current_month) if current_month else {}
    categories = sorted({r.category for r in records})

    drivers: list[CategoryDriver] = []
    for cat in categories:
        cat_series = category_monthly_series(records, cat)
        if not any(v for _, v in cat_series):
            continue
        cat_piece = forecast_series(cat_series)
        current = current_breakdown.get(cat, 0)
        drivers.append(
            CategoryDriver(
                category=cat,
                current_month_minor=current,
                predicted_next_month_minor=cat_piece.predicted_minor,
                delta_minor=cat_piece.predicted_minor - current,
            )
        )
    drivers.sort(key=lambda d: -abs(d.delta_minor))

    # Accuracy: the most recent forecast whose horizon_month is a calendar
    # month that has already fully completed, compared to what actually spent.
    today = datetime.now(timezone.utc).date()
    last_completed_month = today.month - 1 or 12
    last_completed_year = today.year if today.month > 1 else today.year - 1
    last_completed_first = month_str_to_date(f"{last_completed_year:04d}-{last_completed_month:02d}")

    past_forecast = (
        db.query(Forecast)
        .filter(Forecast.user_id == current_user.id, Forecast.horizon_month == last_completed_first)
        .order_by(Forecast.generated_at.desc())
        .first()
    )
    accuracy = None
    if past_forecast:
        month_key = f"{last_completed_year:04d}-{last_completed_month:02d}"
        actual = dict(total_series).get(month_key)
        if actual is not None:
            error_minor = abs(past_forecast.predicted_total_minor - actual)
            error_pct = (error_minor / actual * 100) if actual else None
            accuracy = ForecastAccuracy(
                month=month_key,
                predicted_minor=past_forecast.predicted_total_minor,
                actual_minor=actual,
                error_minor=error_minor,
                error_pct=round(error_pct, 1) if error_pct is not None else None,
            )

    return HorizonForecastResponse(
        months=month_points,
        model_used=model_used,
        is_low_confidence=is_low_confidence,
        history_months=history_months,
        category_drivers=drivers[:3],
        accuracy=accuracy,
    )
