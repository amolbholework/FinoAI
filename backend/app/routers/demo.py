from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import enforce_ip_rate_limit
from app.core.security import (
    create_access_token,
    get_current_user,
    issue_refresh_token,
    set_auth_cookies,
)
from app.demo.seed import seed_demo_dataset
from app.models.base import new_uuid
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/demo", tags=["demo"])
settings = get_settings()


def _to_user_response(db: Session, user: User) -> UserResponse:
    # Local import avoids a circular import with auth.py (which also
    # defines this); duplicating the four-line body would be worse.
    from app.routers.auth import _to_user_response as _shared

    return _shared(db, user)


@router.post("/try", response_model=UserResponse)
def try_demo(request: Request, response: Response, db: Session = Depends(get_db)):
    """Public, no sign-in required — the whole point of a 'Try demo'
    button. Creates a fresh, fully-seeded guest account and signs the
    browser into it directly, same session mechanism as a real sign-in."""
    enforce_ip_rate_limit(request, "demo-try", max_per_minute=10)

    guest_id = new_uuid()
    user = User(
        google_sub=f"demo-guest-{guest_id}",
        email=f"demo-{guest_id}@example.com",
        name="Demo Explorer",
        picture_url=None,
        is_demo=True,
    )
    db.add(user)
    db.flush()
    seed_demo_dataset(db, user.id)

    access_token = create_access_token(user)
    refresh_token = issue_refresh_token(db, user)
    db.commit()
    db.refresh(user)

    set_auth_cookies(response, access_token, refresh_token)
    return _to_user_response(db, user)


@router.post("/enable", response_model=UserResponse)
def enable_test_mode(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Switches a real, signed-in user over to their own shadow demo
    account. The shadow account is created and seeded once, lazily, on
    first use, then reused on every later toggle — this never reads,
    writes, or touches the real account's own data."""
    if current_user.is_demo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This account is already a demo account.")

    if not current_user.demo_shadow_user_id:
        shadow = User(
            google_sub=f"demo-shadow-{current_user.id}",
            email=current_user.email,
            name=current_user.name,
            picture_url=None,
            is_demo=True,
        )
        db.add(shadow)
        db.flush()
        seed_demo_dataset(db, shadow.id)
        current_user.demo_shadow_user_id = shadow.id

    current_user.test_mode_enabled = True
    db.commit()
    db.refresh(current_user)
    return _to_user_response(db, current_user)


@router.post("/disable", response_model=UserResponse)
def disable_test_mode(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.test_mode_enabled = False
    db.commit()
    db.refresh(current_user)
    return _to_user_response(db, current_user)
