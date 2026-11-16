"""Uvicorn entrypoint for the backend service.

Run from this directory::

    uvicorn main:app --host 0.0.0.0 --port 8000

``app`` is the same FastAPI instance exposed by :mod:`app.main`.
"""

from app.main import app

__all__ = ["app"]
