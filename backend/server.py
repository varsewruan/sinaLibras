"""Entrypoint shim.

The real application lives in `app.main`. This module exists so that
hosting environments configured to launch `uvicorn server:app` (e.g. the
default Emergent runner) continue to work after the restructure.
"""

from app.main import app

__all__ = ["app"]
