"""Auth router: bcrypt login, PyJWT session token, current-user lookup."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.config import settings
from app.deps import CurrentUser, DbSession
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut, iso_utc
from app.security import create_access_token, hash_password, verify_password
from app.services.ratelimit import RateLimiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

email_limiter = RateLimiter(settings.login_attempts_per_email, settings.login_window_seconds)
ip_limiter = RateLimiter(settings.login_attempts_per_ip, settings.login_window_seconds)

# Compared against when the email is unknown so a failed login costs the same
# time either way (no account enumeration through response timing).
_DUMMY_HASH = hash_password("sprintline-dummy-password")


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, session: DbSession) -> LoginResponse:
    """Verify email + password against the bcrypt hash and return a JWT."""
    client_host = request.client.host if request.client else "unknown"
    email_allowed = email_limiter.allow(f"email:{payload.email}")
    ip_allowed = ip_limiter.allow(f"ip:{client_host}")
    if not email_allowed or not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many sign-in attempts. Please wait a moment and try again.",
            headers={"Retry-After": str(email_limiter.retry_after())},
        )

    user = session.scalar(select(User).where(func.lower(User.email) == payload.email))
    if user is None:
        verify_password(payload.password, _DUMMY_HASH)
        raise _invalid_credentials()
    if not verify_password(payload.password, user.password_hash):
        raise _invalid_credentials()

    token, expires_at = create_access_token(user.id)
    return LoginResponse(
        token=token,
        expires_at=iso_utc(expires_at) or "",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def read_current_user(user: CurrentUser) -> UserOut:
    """Return the profile behind the supplied Bearer token."""
    return UserOut.model_validate(user)
