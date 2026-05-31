"""
Health endpoints for load balancers / Kubernetes / Docker healthchecks.

- /healthz : liveness — is the process up?
- /readyz  : readiness — can it serve traffic? (pings Mongo)

Split because a process can be alive (no crash) but unable to serve
(DB down). Kubernetes uses each signal differently: liveness failure
restarts the pod; readiness failure pulls it from the load balancer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/readyz", summary="Readiness probe (pings Mongo)")
async def readiness(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict[str, str]:
    try:
        await db.command("ping")
    except Exception as exc:  # pragma: no cover — exercised in integration tests
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database_unreachable: {exc}",
        )
    return {"status": "ready"}
