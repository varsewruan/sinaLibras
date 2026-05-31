"""
Typed application settings loaded from environment variables.

We use pydantic-settings instead of reading os.environ directly so that:
  - missing required values fail fast at boot with a clear validation error
    (instead of KeyError deep inside a request handler);
  - types are coerced (e.g. CORS_ORIGINS arrives as a comma-separated string
    and becomes a list[str]);
  - tests can override settings via env vars or by instantiating Settings(**overrides).

A single cached Settings instance is exposed via get_settings(). FastAPI
dependencies can `Depends(get_settings)` to receive it without reloading
the .env file on every request.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


Environment = Literal["development", "staging", "production", "test"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- Database ---------------------------------------------------------
    MONGO_URL: str = Field(..., description="MongoDB connection URI")
    DB_NAME: str = Field(..., min_length=1, description="Mongo database name")
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = Field(default=5_000, ge=100)
    MONGO_MAX_POOL_SIZE: int = Field(default=50, ge=1)

    # ---- HTTP / CORS ------------------------------------------------------
    # Stored as list[str]. Accepts a comma-separated string in the env var.
    # NoDecode tells pydantic-settings to skip its default JSON parsing so
    # our @field_validator(mode="before") receives the raw string.
    # NEVER allow "*" together with credentials — the CORS spec forbids it
    # and browsers reject the preflight.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # ---- Runtime ----------------------------------------------------------
    ENVIRONMENT: Environment = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # ---- API metadata -----------------------------------------------------
    API_TITLE: str = Field(default="SINALibras API")
    API_VERSION: str = Field(default="0.1.0")
    API_PREFIX: str = Field(default="/api")

    # ---- JWT --------------------------------------------------------------
    # JWT_SECRET MUST be a long random string. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    # Never commit the production value.
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = Field(default="HS256")
    ACCESS_TOKEN_TTL_MINUTES: int = Field(default=15, ge=1)
    REFRESH_TOKEN_TTL_DAYS: int = Field(default=7, ge=1)

    # ---- Cookies (auth tokens live in httpOnly cookies) -------------------
    # In production over HTTPS, COOKIE_SECURE must be True.
    # SameSite=Lax is correct when frontend and backend share a registrable
    # domain (e.g. app.example.com + api.example.com). For cross-site
    # deployments (different eTLD+1), switch to "none" and ensure HTTPS.
    COOKIE_SECURE: bool = Field(default=False)
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = Field(default="lax")
    COOKIE_DOMAIN: str | None = Field(default=None)

    # ---- Rate limiting ----------------------------------------------------
    RATE_LIMIT_LOGIN: str = Field(default="5/minute")
    RATE_LIMIT_REGISTER: str = Field(default="3/minute")
    RATE_LIMIT_REFRESH: str = Field(default="10/minute")

    # ---- SPA hosting ------------------------------------------------------
    # When set, app.main serves the built SPA at "/" and uses an HTML5
    # history fallback for client-side routes. /api/* is unaffected.
    # Unset in pure-API deploys.
    FRONTEND_BUILD_DIR: str | None = Field(default=None)

    # ---- Sign assets ------------------------------------------------------
    # Directory containing the catalog's per-sign images / SVG placeholders
    # (produced by scripts/build_sign_assets.py). Mounted at /signs/*.
    # Path is resolved relative to the working dir if not absolute.
    SIGNS_DIR: str = Field(default="static/signs")

    # ----------------------------------------------------------------------
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> list[str]:
        """Accept either a comma-separated string or a list."""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("CORS_ORIGINS must be a list or comma-separated string")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _no_wildcard_with_credentials(cls, value: list[str]) -> list[str]:
        # Cookies are sent with credentials; "*" is invalid in that mode.
        if "*" in value:
            raise ValueError(
                "CORS_ORIGINS must not contain '*' — explicit origins are required "
                "because the API uses credentialed requests (httpOnly cookies)."
            )
        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return upper

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_prod(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance. Override in tests with `get_settings.cache_clear()`."""
    return Settings()
