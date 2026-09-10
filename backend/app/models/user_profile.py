from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import new_uuid, utcnow

ONBOARDING_STATUSES = ("not_started", "in_progress", "completed", "skipped")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(16), default="not_started", nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Keyed by question id — the raw source of truth. risk_band/literacy_level/etc
    # below are derived from this via scoring.py and can always be recomputed.
    answers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    risk_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    literacy_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    life_stage: Mapped[str | None] = mapped_column(String(16), nullable=True)
    income_stability: Mapped[str | None] = mapped_column(String(16), nullable=True)
    investment_experience: Mapped[str | None] = mapped_column(String(16), nullable=True)
    goals: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
