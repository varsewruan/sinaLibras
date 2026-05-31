from __future__ import annotations

from app.models.status import StatusCheck
from app.repositories.base import BaseRepository


class StatusRepository(BaseRepository[StatusCheck]):
    collection_name = "status_checks"
    model = StatusCheck
