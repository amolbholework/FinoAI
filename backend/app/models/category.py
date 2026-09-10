from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, or_
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import new_uuid

SYSTEM_CATEGORIES = [
    "Food",
    "Rent",
    "Transport",
    "Utilities",
    "Shopping",
    "Health",
    "Entertainment",
    "Income",
    "Other",
]


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_categories_user_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    # NULL for system categories (shared, seeded once at startup). Set for a
    # user's own custom categories — never shared across users.
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


def owned_or_system(user_id: str):
    """Filter expression: a user's own categories plus the shared system
    ones. `Category.user_id.in_((user_id, None))` looks equivalent but SQL's
    IN never matches NULL, so system categories would silently vanish."""
    return or_(Category.user_id == user_id, Category.user_id.is_(None))
