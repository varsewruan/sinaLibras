"""
Authentication service — the only place that knows how to turn credentials
into a User and how to mint/refresh tokens.

Routes are thin shells around this; tests can exercise the rules without
spinning up FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth import LoginRequest, RegisterRequest
from app.models.user import User
from app.repositories.user_repo import UserRepository


class AuthError(Exception):
    """Domain-level auth failures (wrong creds, taken email, stale token, etc.).

    `code` is the machine contract — it's what the SPA and the tests switch
    on, so it stays in English and must not be translated. `message` is what
    a person reads on screen, so it's in Portuguese like the rest of the app.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# Pre-computed at import time so login latency for an unknown email matches
# the bcrypt work of a real login. Value is irrelevant — only the cost matters.
_DUMMY_HASH = hash_password("timing-equalizer-dummy")


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, *, settings: Settings, users: UserRepository) -> None:
        self.settings = settings
        self.users = users

    # ------------------ Registration / Login -------------------------------

    async def register(self, payload: RegisterRequest) -> tuple[User, IssuedTokens]:
        existing = await self.users.get_by_email(payload.email)
        if existing is not None:
            raise AuthError("email_taken", "Este e-mail já está cadastrado.")

        user = User(
            email=payload.email,
            name=payload.name,
            hashed_password=hash_password(payload.password),
        )
        await self.users.insert(user)
        return user, self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> tuple[User, IssuedTokens]:
        user = await self.users.get_by_email(payload.email)
        # Verify even when user is None, to keep timing roughly constant
        # against an attacker probing for valid emails. _DUMMY_HASH is a
        # real bcrypt hash so checkpw does the same work either branch.
        if user is None:
            verify_password(payload.password, _DUMMY_HASH)
            raise AuthError("invalid_credentials", "E-mail ou senha incorretos.")

        if not verify_password(payload.password, user.hashed_password):
            raise AuthError("invalid_credentials", "E-mail ou senha incorretos.")

        return user, self._issue_tokens(user)

    # ------------------ Refresh / Logout -----------------------------------

    async def refresh(self, refresh_token: str) -> tuple[User, IssuedTokens]:
        try:
            payload = decode_token(
                settings=self.settings,
                token=refresh_token,
                expected_type="refresh",
            )
        except TokenError as exc:
            # The TokenError text ("invalid_token: Signature has expired") was
            # being handed straight to the client. It's a diagnostic, not a
            # sentence for a user — and it leaks token internals. `code` still
            # distinguishes this from every other auth failure.
            raise AuthError(
                "invalid_refresh_token", "Sua sessão expirou. Entre novamente."
            ) from exc

        user = await self.users.get(payload["sub"])
        if user is None:
            raise AuthError("user_not_found", "Esta conta não existe mais.")

        if payload["tv"] != user.token_version:
            raise AuthError("token_revoked", "Sua sessão foi encerrada. Entre novamente.")

        return user, self._issue_tokens(user)

    async def logout_everywhere(self, user: User) -> None:
        """Bump token_version so every existing token (access + refresh) becomes invalid."""
        await self.users.update_fields(
            user.id,
            {"token_version": user.token_version + 1},
        )

    # ------------------ Internals ------------------------------------------

    def _issue_tokens(self, user: User) -> IssuedTokens:
        return IssuedTokens(
            access_token=create_access_token(
                settings=self.settings,
                user_id=user.id,
                token_version=user.token_version,
            ),
            refresh_token=create_refresh_token(
                settings=self.settings,
                user_id=user.id,
                token_version=user.token_version,
            ),
        )
