"""
Password hashing and JWT issuance / verification.

Design notes:
  - bcrypt directly (no passlib). passlib 1.7.4 emits a noisy
    AttributeError-warning against bcrypt >= 4.1 because of an internal
    version probe. Using bcrypt's own API sidesteps it and keeps the
    dependency set smaller.
  - PyJWT (not python-jose). python-jose has a CVE around algorithm
    confusion and is no longer maintained.
  - HS256 by default. Switch to RS256 when you need to give a third party
    a public key to verify our tokens without sharing the secret.
  - Tokens carry a token_version (`tv`) claim. Bumping User.token_version
    invalidates every previously-issued token for that user — a stateless,
    O(1) "logout everywhere" / "password rotated" mechanism.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings

TokenType = Literal["access", "refresh"]


# -------------------- Password ----------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash (cost 12 by default). UTF-8 safe."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison. Never short-circuit on length."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Malformed hash (e.g. legacy import) — fail closed.
        return False


# -------------------- JWT ---------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_payload(
    *,
    subject: str,
    token_type: TokenType,
    token_version: int,
    ttl: timedelta,
) -> dict[str, Any]:
    now = _now()
    return {
        "sub": subject,
        "type": token_type,
        "tv": token_version,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "jti": str(uuid.uuid4()),
    }


def create_access_token(*, settings: Settings, user_id: str, token_version: int) -> str:
    payload = _build_payload(
        subject=user_id,
        token_type="access",
        token_version=token_version,
        ttl=timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES),
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(*, settings: Settings, user_id: str, token_version: int) -> str:
    payload = _build_payload(
        subject=user_id,
        token_type="refresh",
        token_version=token_version,
        ttl=timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class TokenError(Exception):
    """Raised when a token can't be decoded, is expired, or has the wrong type."""


def decode_token(
    *,
    settings: Settings,
    token: str,
    expected_type: TokenType,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise TokenError(f"invalid_token: {exc}") from exc

    if payload.get("type") != expected_type:
        raise TokenError(
            f"wrong_token_type: expected {expected_type}, got {payload.get('type')!r}"
        )
    if "sub" not in payload or "tv" not in payload:
        raise TokenError("malformed_token: missing claims")
    return payload
