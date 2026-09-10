from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import new_uuid, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    # The stable Google subject identifier — the actual identity, since email
    # can change (or be reused after an account is deleted on Google's side).
    google_sub: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Bumped on logout / "sign out everywhere" so previously-issued refresh
    # tokens (which embed the version they were minted with) stop validating.
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)

    # --- Demo/test mode ---
    # is_demo=True marks a row that IS a demo account: either an anonymous
    # "Try demo" guest (no real Google identity behind it) or the seeded
    # shadow account a real user's test-mode toggle points at. Isolation is
    # by namespace (a whole separate user_id), not a per-row flag on every
    # transaction/goal/etc — every existing user_id-scoped query already
    # gets this for free, nothing else in the codebase has to know demo
    # mode exists.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Set only on a real (non-demo) user once they first enable test mode —
    # points at their own personal, lazily-seeded shadow demo account,
    # reused on every later toggle rather than reseeded each time.
    demo_shadow_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    # Whether a real user is CURRENTLY viewing their shadow demo account.
    # Meaningless (always False) on an is_demo=True row itself.
    test_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
