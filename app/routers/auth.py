"""Auth endpoints: register + login + me (B7, B10).

Stateless JWT (V1): logout is client-side token discard — no server endpoint.
Rate limiting (B10): in-memory sliding window on login (~5/min/IP).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.dependencies import Db, get_current_user
from app.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

# --- B10: login rate limit state (single-process V1; use slowapi/Redis later) ---
_LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_S = 60.0


def _check_login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _LOGIN_ATTEMPTS[ip]
    while window and now - window[0] > LOGIN_RATE_WINDOW_S:
        window.popleft()
    if len(window) >= LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a minute.",
        )
    window.append(now)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class RegisterResponse(UserResponse):
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


CurrentUser = Annotated[User, Depends(get_current_user)]


def _issue_token(user: User) -> str:
    return create_access_token(sub=user.id, email=user.email)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Db) -> RegisterResponse:
    """Create an account; returns the user + a ready-to-use access token."""
    email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = _issue_token(user)
    return RegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        access_token=token,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Db) -> TokenResponse:
    """Verify credentials; uniform 401 reveals nothing about which field failed."""
    _check_login_rate_limit(request)
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return TokenResponse(access_token=_issue_token(user))


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
