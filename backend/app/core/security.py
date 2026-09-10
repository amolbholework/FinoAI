"""Google ID token verification, our own access/refresh JWTs, and the
current-user dependency every protected route depends on."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.base import new_uuid, utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User

settings = get_settings()

ACCESS_COOKIE_NAME = "fp_access"
REFRESH_COOKIE_NAME = "fp_refresh"
JWT_ALGORITHM = "HS256"

_GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def _aware(dt: datetime) -> datetime:
    """SQLite drops tzinfo on DateTime(timezone=True) columns on read-back;
    treat a naive value as UTC (what it always was) rather than let it blow
    up comparisons against utcnow()."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class GoogleIdentity:
    sub: str
    email: str
    name: str
    picture: str | None


def verify_google_id_token(token: str) -> GoogleIdentity:
    """Verifies signature (against Google's public keys), audience, issuer,
    and expiry. Never trust an identity claim without doing this."""
    try:
        claims = google_id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google ID token.") from exc

    if claims.get("iss") not in _GOOGLE_ISSUERS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unexpected token issuer.")

    return GoogleIdentity(
        sub=claims["sub"],
        email=claims["email"],
        name=claims.get("name") or claims["email"],
        picture=claims.get("picture"),
    )


def create_access_token(user: User) -> str:
    expire = utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    # jti guarantees two tokens minted for the same user in the same second
    # still differ — JWT encoding is otherwise deterministic for identical claims.
    claims = {"sub": user.id, "tv": user.token_version, "jti": new_uuid(), "exp": expire}
    return jwt.encode(claims, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def issue_refresh_token(db: Session, user: User) -> str:
    jti = new_uuid()
    expires_at = utcnow() + timedelta(days=settings.refresh_token_ttl_days)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    return jwt.encode({"sub": user.id, "jti": jti, "exp": expires_at}, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str, str] | None:
    """Single-use rotation with reuse detection. Returns (user, new_access,
    new_refresh) on success, None if the token is invalid/expired/reused
    (caller should 401 and clear cookies)."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None

    row = db.query(RefreshToken).filter(RefreshToken.jti == claims.get("jti")).first()
    if row is None:
        return None

    if row.revoked_at is not None:
        # This jti was already rotated away once — someone is replaying an
        # old refresh token. Revoke every outstanding session for the user
        # and bump token_version so live access tokens die too.
        user = db.query(User).filter(User.id == row.user_id).first()
        if user is not None:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            ).update({"revoked_at": utcnow()})
            user.token_version += 1
            db.commit()
        return None

    if _aware(row.expires_at) < utcnow():
        return None

    user = db.query(User).filter(User.id == row.user_id).first()
    if user is None:
        return None

    row.revoked_at = utcnow()
    new_access = create_access_token(user)
    new_refresh = issue_refresh_token(db, user)
    db.commit()
    return user, new_access, new_refresh


def revoke_refresh_token(db: Session, token: str) -> None:
    """Best-effort revoke of a specific refresh token by its jti (used on logout)."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return
    db.query(RefreshToken).filter(RefreshToken.jti == claims.get("jti")).update({"revoked_at": utcnow()})


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")

    claims = decode_access_token(token)
    if claims is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session.")

    user = db.query(User).filter(User.id == claims.get("sub")).first()
    if user is None or user.token_version != claims.get("tv"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session.")

    return user


def get_effective_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """The user whose DATA should be read/written for this request.

    Identity endpoints (auth, profile, onboarding) always use
    get_current_user directly — this is only for routers that touch a
    user's financial data (transactions, budgets, goals, forecasts,
    categories, reports, analysis, AI, Fino). When the real, signed-in
    user has test mode toggled on, every one of those routes transparently
    operates on their separate, pre-seeded shadow demo account instead —
    same query code, different namespace, so a demo session can never
    read, write, or delete a byte of the real account's data.
    """
    if not current_user.test_mode_enabled or current_user.is_demo:
        return current_user

    if current_user.demo_shadow_user_id:
        shadow = db.query(User).filter(User.id == current_user.demo_shadow_user_id).first()
        if shadow is not None:
            return shadow

    # test_mode_enabled with no (or a dangling) shadow user shouldn't
    # happen — /api/demo/enable always creates one first — but fail safe
    # to the real account rather than 500 or silently invent one here.
    return current_user


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # Secure cookies are never sent back over plain HTTP — that's correct in
    # production (HTTPS everywhere) but would silently break every local
    # dev/test session, since neither the test client nor a plain
    # http://localhost dev server is an HTTPS origin.
    secure = settings.app_env != "development"
    # SameSite=Lax only ever sends a cookie on a top-level navigation, never
    # on a cross-site fetch/XHR — which is exactly how the frontend (Netlify)
    # talks to this API (Render), on a different registrable domain. Without
    # SameSite=None here, every credentialed request after the initial
    # sign-in/demo call silently drops the cookie and looks like an
    # unauthenticated session. None requires Secure, which is why this only
    # flips once we're already requiring HTTPS (production); local dev stays
    # same-site (localhost:5173 -> localhost:8000) so Lax is correct there.
    samesite = "none" if secure else "lax"
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        max_age=settings.access_token_ttl_minutes * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
