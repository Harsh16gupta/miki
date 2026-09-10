"""Password hashing (Argon2id) + JWT creation/verification (B5).

Fail-fast on missing ``JWT_SECRET_KEY`` — same pattern as
``app/database.py`` for ``DATABASE_URL``. Never run with a default secret.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Copy .env.example to .env and set it."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

_password_hash = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True iff the plaintext matches the stored hash."""
    try:
        return _password_hash.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(
    sub: int, email: str, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT with ``sub`` (user id as string), email, iat, exp."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(sub),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode + verify a JWT. Raises ``jwt.InvalidTokenError`` on failure."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
