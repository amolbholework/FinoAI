from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import new_uuid, utcnow


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # Backs the dedup check (same date + amount + description) done on CSV re-upload.
        # user_id leads so dedup stays scoped per-user rather than global.
        Index("ix_transactions_dedup", "user_id", "date", "amount_minor", "raw_description"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Signed, smallest currency unit (paise for INR). Negative = spend, positive = income.
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    # True once a human has confirmed the category (manual entry, or an override on
    # an auto-categorized row). Only these rows are used to retrain the classifier.
    category_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")  # "csv" | "manual"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    category: Mapped["Category | None"] = relationship("Category")
