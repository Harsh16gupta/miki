"""FastAPI auth dependencies (B6).

``get_current_user`` enforces authentication (401 on missing/invalid token).
``get_optional_user`` returns ``None`` for guest-compatible routes.
"""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as DbSession

from app.auth.security import decode_access_token
from app.database import SessionLocal
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db():
    """Per-request DB session (closed after the request)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[DbSession, Depends(get_db)]
OptionalToken = Annotated[str | None, Depends(oauth2_scheme)]


def _user_from_token(db: DbSession, token: str) -> User | None:
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        return None
    sub = payload.get("sub")
    try:
        user_id = int(sub) if sub is not None else None
    except (TypeError, ValueError):
        return None
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(token: OptionalToken, db: Db) -> User:
    """Require a valid Bearer token; 401 otherwise (no user-enumeration leak)."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _user_from_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(token: OptionalToken, db: Db) -> User | None:
    """Return the authenticated user, or None when no/invalid token (guest)."""
    if not token:
        return None
    return _user_from_token(db, token)
