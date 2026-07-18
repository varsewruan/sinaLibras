"""
/auth/* endpoints.

Tokens travel in httpOnly cookies — never in the response body. The SPA
gets a UserPublic JSON to hydrate its AuthContext, and the browser handles
cookies invisibly.

Rate limits live in Settings (RATE_LIMIT_*). Tune them per environment.
"""

from typing import Optional

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Request, Response, status

from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.deps import get_auth_service, get_current_user
from app.models.auth import AuthResponse, LoginRequest, RegisterRequest
from app.models.user import User, UserPublic
from app.services.auth_service import AuthError, AuthService, IssuedTokens

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


# ---------------- helpers ---------------------------------------------------

def _set_auth_cookies(
    response: Response,
    tokens: IssuedTokens,
    settings: Settings,
) -> None:
    common = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN,
        "path": "/",
    }
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=tokens.access_token,
        max_age=settings.ACCESS_TOKEN_TTL_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=tokens.refresh_token,
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
        **common,
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            key=name,
            path="/",
            domain=settings.COOKIE_DOMAIN,
        )


def _raise(error: AuthError) -> None:
    code_to_status = {
        "email_taken": status.HTTP_409_CONFLICT,
        "invalid_credentials": status.HTTP_401_UNAUTHORIZED,
        "invalid_refresh_token": status.HTTP_401_UNAUTHORIZED,
        "token_revoked": status.HTTP_401_UNAUTHORIZED,
        "user_not_found": status.HTTP_401_UNAUTHORIZED,
    }
    raise HTTPException(
        status_code=code_to_status.get(error.code, status.HTTP_400_BAD_REQUEST),
        detail={"code": error.code, "message": error.message},
    )


# ---------------- endpoints -------------------------------------------------

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and log in",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_REGISTER)
async def register(
    request: Request,  # required by slowapi; must be first
    response: Response,
    # Body(...) is explicit because slowapi's @limit decorator confuses
    # FastAPI's body-vs-query inference for Pydantic models.
    payload: RegisterRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    try:
        user, tokens = await service.register(payload)
    except AuthError as exc:
        _raise(exc)
    _set_auth_cookies(response, tokens, settings)
    return AuthResponse(user=UserPublic.from_user(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email + password",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    try:
        user, tokens = await service.login(payload)
    except AuthError as exc:
        _raise(exc)
    _set_auth_cookies(response, tokens, settings)
    return AuthResponse(user=UserPublic.from_user(user))


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Rotate access + refresh tokens",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_REFRESH)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE),
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "missing_refresh_token",
                "message": "Entre na sua conta para continuar.",
            },
        )
    try:
        user, tokens = await service.refresh(refresh_token)
    except AuthError as exc:
        _raise(exc)
    _set_auth_cookies(response, tokens, settings)
    return AuthResponse(user=UserPublic.from_user(user))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out — bumps token_version, clears cookies",
)
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> Response:
    await service.logout_everywhere(user)
    _clear_auth_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Current authenticated user",
)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.from_user(user)
