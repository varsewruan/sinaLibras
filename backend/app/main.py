"""
FastAPI application factory.

The factory pattern (create_app) lets tests build an isolated app with a
different Settings instance, and keeps module-level side effects to a
minimum: importing `app.main` only constructs the app, it doesn't open
connections — that happens in the lifespan.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.errors import validation_exception_handler
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import limiter
from app.db.mongo import close_mongo_connection, connect_to_mongo, ensure_indexes
from app.routers import achievements, auth, health, learning, progress, ranking, shop, users

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = get_settings()
    setup_logging(settings)
    logger.info(
        "startup_begin",
        env=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        cors_origins=settings.CORS_ORIGINS,
    )

    db = await connect_to_mongo(settings)
    await ensure_indexes(db)

    logger.info("startup_complete")
    try:
        yield
    finally:
        logger.info("shutdown_begin")
        await close_mongo_connection()
        logger.info("shutdown_complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        lifespan=lifespan,
    )

    # Rate limiter — must be installed BEFORE routes register their @limiter.limit decorators.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Renders pydantic's 422s in Portuguese. Same status and body shape as
    # FastAPI's default handler — only the `msg` text changes.
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # CORS — registered BEFORE any router is included.
    # `allow_origins` is the validated explicit list from Settings (never "*").
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix=settings.API_PREFIX)

    @api.get("/", summary="Root")
    async def root() -> dict[str, str]:
        return {"name": settings.API_TITLE, "version": settings.API_VERSION}

    api.include_router(health.router)
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(learning.router)
    api.include_router(progress.router)
    api.include_router(ranking.router)
    api.include_router(achievements.router)
    api.include_router(shop.router)

    app.include_router(api)

    # Signs MUST mount before the SPA fallback, otherwise the catch-all
    # swallows /signs/* before StaticFiles can answer.
    _mount_signs(app, settings)
    _mount_spa_if_configured(app, settings)
    return app


def _mount_signs(app: FastAPI, settings: Settings) -> None:
    """
    Mount the sign-asset directory at /signs/*. Always-on regardless of
    SPA hosting — dev (split-host) and prod (single-host) both rely on it.
    """
    signs_dir = Path(settings.SIGNS_DIR)
    if not signs_dir.is_dir():
        logger.warning("signs_dir_missing", path=str(signs_dir))
        return
    app.mount("/signs", StaticFiles(directory=str(signs_dir)), name="signs")
    logger.info("signs_mounted", path=str(signs_dir))


def _mount_spa_if_configured(app: FastAPI, settings: Settings) -> None:
    """
    In single-host deploys (Fly.io), the same FastAPI process serves both
    /api/* and the built React bundle. Skipped when FRONTEND_BUILD_DIR is
    unset (pure-API mode used in dev compose and tests).

    Order matters: /api/* routes are already registered above and take
    precedence; the SPA fallback only fires for unmatched paths.
    """
    if not settings.FRONTEND_BUILD_DIR:
        return

    build_dir = Path(settings.FRONTEND_BUILD_DIR)
    if not build_dir.is_dir():
        logger.warning("spa_build_dir_missing", path=str(build_dir))
        return

    index_file = build_dir / "index.html"
    if not index_file.is_file():
        logger.warning("spa_index_missing", path=str(index_file))
        return

    # CRA emits hashed asset filenames under /static — mount with the same
    # path so the index.html references resolve unchanged.
    static_dir = build_dir / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static-assets")

    api_prefix = settings.API_PREFIX.strip("/")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        # A request to a *registered* /api/* route is matched earlier and
        # never reaches here. An *unregistered* /api/* path WOULD fall
        # through to this catch-all, returning index.html with a 200 — which
        # is what callers JSON.parse blowing up downstream. So guard it.
        if api_prefix and (full_path == api_prefix or full_path.startswith(f"{api_prefix}/")):
            raise HTTPException(status_code=404)
        # Reject obvious file requests (e.g. /robots.txt) with a real 404 so
        # crawlers don't get index.html with a 200.
        if "." in full_path.rsplit("/", 1)[-1]:
            candidate = build_dir / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            raise HTTPException(status_code=404)
        return FileResponse(index_file)

    logger.info("spa_mounted", build_dir=str(build_dir))


app = create_app()
