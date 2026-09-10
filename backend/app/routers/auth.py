from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    create_access_token,
    get_current_user,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    set_auth_cookies,
    verify_google_id_token,
)
from app.models.budget import Budget
from app.models.category import Category
from app.models.fino_message import FinoMessage
from app.models.forecast import Forecast
from app.models.goal import Goal
from app.models.recommendation import Recommendation
from app.models.refresh_token import RefreshToken
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import GoogleSignInRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_user_response(db: Session, user: User) -> UserResponse:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
        created_at=user.created_at,
        onboarding_status=profile.status if profile else "not_started",
        is_demo=user.is_demo,
        test_mode_enabled=user.test_mode_enabled,
    )


def _claim_orphaned_data(db: Session, user_id: str) -> None:
    """Assigns every currently-unscoped row to the first user account ever
    created. This app predates auth — this data was never in localStorage,
    it's already in the DB, just unscoped — so this is the real equivalent
    of "import my local data" for whoever signs in first."""
    db.query(Transaction).filter(Transaction.user_id.is_(None)).update({"user_id": user_id})
    db.query(Budget).filter(Budget.user_id.is_(None)).update({"user_id": user_id})
    db.query(Goal).filter(Goal.user_id.is_(None)).update({"user_id": user_id})
    db.query(Category).filter(Category.user_id.is_(None), Category.is_system.is_(False)).update({"user_id": user_id})


@router.post("/google", response_model=UserResponse)
def sign_in_with_google(payload: GoogleSignInRequest, response: Response, db: Session = Depends(get_db)):
    identity = verify_google_id_token(payload.id_token)

    user = db.query(User).filter(User.google_sub == identity.sub).first()
    if user is None:
        is_first_ever_user = db.query(User).count() == 0
        user = User(google_sub=identity.sub, email=identity.email, name=identity.name, picture_url=identity.picture)
        db.add(user)
        db.flush()  # assigns user.id without committing yet
        if is_first_ever_user:
            _claim_orphaned_data(db, user.id)
    else:
        user.email = identity.email
        user.name = identity.name
        user.picture_url = identity.picture

    access_token = create_access_token(user)
    refresh_token = issue_refresh_token(db, user)
    db.commit()
    db.refresh(user)

    set_auth_cookies(response, access_token, refresh_token)
    return _to_user_response(db, user)


@router.post("/refresh", response_model=UserResponse)
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh session.")

    result = rotate_refresh_token(db, token)
    if result is None:
        clear_auth_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired — please sign in again.")

    user, access_token, refresh_token = result
    set_auth_cookies(response, access_token, refresh_token)
    return _to_user_response(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token:
        revoke_refresh_token(db, token)

    # Belt-and-suspenders: bump token_version so the user is fully signed
    # out (including other sessions' access tokens) even without the cookie.
    current_user.token_version += 1
    db.commit()

    clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_user_response(db, current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently deletes the account and every row it owns. User-owned
    categories only — system categories (user_id IS NULL) are shared and
    stay put for everyone else. If this account has a linked shadow demo
    account (from ever enabling test mode), that gets wiped too — nothing
    should survive a delete just because it lived in the demo namespace."""

    def _delete_all_owned_rows(uid: str) -> None:
        db.query(Transaction).filter(Transaction.user_id == uid).delete()
        db.query(Budget).filter(Budget.user_id == uid).delete()
        db.query(Goal).filter(Goal.user_id == uid).delete()
        db.query(Forecast).filter(Forecast.user_id == uid).delete()
        db.query(Recommendation).filter(Recommendation.user_id == uid).delete()
        db.query(Category).filter(Category.user_id == uid).delete()
        db.query(RefreshToken).filter(RefreshToken.user_id == uid).delete()
        db.query(UserProfile).filter(UserProfile.user_id == uid).delete()
        db.query(FinoMessage).filter(FinoMessage.user_id == uid).delete()

    if current_user.demo_shadow_user_id:
        shadow_id = current_user.demo_shadow_user_id
        _delete_all_owned_rows(shadow_id)
        db.query(User).filter(User.id == shadow_id).delete()

    _delete_all_owned_rows(current_user.id)
    db.delete(current_user)
    db.commit()

    clear_auth_cookies(response)
