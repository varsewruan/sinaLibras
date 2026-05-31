"""
Rate-limit singleton used by /auth/* routes.

Stored separately so it's importable without circular deps. Uses in-memory
storage — fine for single-instance dev. For multi-instance prod, swap the
storage backend to Redis: `Limiter(key_func=..., storage_uri="redis://...")`.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
