from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import new_uuid, utcnow


class Advice(Base):
    """A generated /api/advice response, cached per user keyed on a hash of
    the input summary — separate table from `recommendations` (the older
    /ai/recommendations feature) so the two run fully alongside each other
    with no shared cache keys or schema coupling."""

    __tablename__ = "advice"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    data_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)


class AdviceActionState(Base):
    """Per-recommendation dismiss/done state, addressed by
    (advice_id, recommendation_index) rather than by recommendation text —
    AI-generated wording isn't a stable key, but the index within one
    cached Advice row is."""

    __tablename__ = "advice_action_states"
    __table_args__ = (UniqueConstraint("advice_id", "recommendation_index", name="uq_advice_action_state"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    advice_id: Mapped[str] = mapped_column(String(36), ForeignKey("advice.id"), nullable=False, index=True)
    recommendation_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # "dismissed" | "done"
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
