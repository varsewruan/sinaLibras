"""
Status-check endpoint. Kept from the original template as a thin smoke test
for the full request → repository → Mongo pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_status_repo
from app.models.status import StatusCheck, StatusCheckCreate
from app.repositories.status_repo import StatusRepository

router = APIRouter(prefix="/status", tags=["status"])


@router.post(
    "",
    response_model=StatusCheck,
    status_code=status.HTTP_201_CREATED,
    summary="Record a status check",
)
async def create_status_check(
    payload: StatusCheckCreate,
    repo: StatusRepository = Depends(get_status_repo),
) -> StatusCheck:
    obj = StatusCheck(client_name=payload.client_name)
    return await repo.insert(obj)


@router.get(
    "",
    response_model=list[StatusCheck],
    summary="List recent status checks (paginated)",
)
async def list_status_checks(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    repo: StatusRepository = Depends(get_status_repo),
) -> list[StatusCheck]:
    return await repo.list(sort=[("created_at", -1)], limit=limit, skip=skip)
