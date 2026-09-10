from sqlalchemy.orm import Session

from app.analysis.types import TxnRecord
from app.forecasting.series import category_monthly_series, month_str_to_date, next_month_str, total_monthly_series
from app.forecasting.service import forecast_series
from app.models.category import Category
from app.models.forecast import Forecast
from app.models.transaction import Transaction


def load_records(db: Session, user_id: str) -> list[TxnRecord]:
    rows = (
        db.query(Transaction.date, Transaction.amount_minor, Category.name)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(Transaction.user_id == user_id)
        .all()
    )
    return [TxnRecord(date=d, amount_minor=amt, category=cat or "Other") for d, amt, cat in rows]


def generate_forecast(db: Session, user_id: str) -> Forecast:
    records = load_records(db, user_id)

    total_series = total_monthly_series(records)
    total_piece = forecast_series(total_series)

    categories = sorted({r.category for r in records})
    per_category_breakdown: dict[str, dict] = {}
    for category in categories:
        series = category_monthly_series(records, category)
        # Skip categories with no spend history at all — nothing to forecast.
        if not any(v for _, v in series):
            continue
        piece = forecast_series(series)
        per_category_breakdown[category] = {
            "predicted_minor": piece.predicted_minor,
            "low_minor": piece.low_minor,
            "high_minor": piece.high_minor,
            "model_used": piece.model_used,
        }

    horizon_month_str = next_month_str(total_series[-1][0]) if total_series else next_month_str("2000-01")

    forecast = Forecast(
        user_id=user_id,
        horizon_month=month_str_to_date(horizon_month_str),
        predicted_total_minor=total_piece.predicted_minor,
        confidence_low_minor=total_piece.low_minor,
        confidence_high_minor=total_piece.high_minor,
        per_category_breakdown=per_category_breakdown,
        model_used=total_piece.model_used,
        is_low_confidence=total_piece.is_low_confidence,
        mae=total_piece.mae,
        mape=total_piece.mape,
        benchmark_model=total_piece.benchmark_model,
        benchmark_mae=total_piece.benchmark_mae,
        benchmark_mape=total_piece.benchmark_mape,
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast
