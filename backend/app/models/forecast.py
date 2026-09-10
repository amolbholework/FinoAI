from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import new_uuid, utcnow


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    horizon_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # first-of-month being forecast

    predicted_total_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_low_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_high_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    # {category_name: {predicted_minor, low_minor, high_minor}}
    per_category_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)

    model_used: Mapped[str] = mapped_column(String(32), nullable=False)  # "prophet" | "average_fallback"
    is_low_confidence: Mapped[bool] = mapped_column(default=False, nullable=False)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ARIMA is run purely as a comparison baseline (never selected as model_used) —
    # kept alongside Prophet's own error so the report can cite both, per the brief.
    benchmark_model: Mapped[str | None] = mapped_column(String(32), nullable=True)
    benchmark_mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_mape: Mapped[float | None] = mapped_column(Float, nullable=True)
