"""FastAPI application entrypoint.

``app`` at module level — run with ``uvicorn main:app`` (or ``uvicorn
app.main:app``) from the backend directory. The lifespan hook creates the schema
and seeds the demo workspace when the database is empty, so every launch path
reaches a populated app with no manual step.
"""

from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db import SessionLocal, ensure_schema
from app.landing import render_landing
from app.models import Issue, Project, Sprint, User
from app.routers import activity, auth, comments, issues, meta, roadmap, sprints
from app.seed import describe_seed, run_seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sprintline")

STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
}


def bootstrap_database() -> None:
    """Create tables and seed the demo workspace once (idempotent)."""
    ensure_schema()
    if not settings.auto_seed:
        return
    with SessionLocal() as session:
        summary = run_seed(session)
    print(describe_seed(summary), flush=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Boot path: schema + demo seed, then serve."""
    bootstrap_database()
    logger.info("Sprintline API ready — bind 0.0.0.0, docs at /docs")
    yield


app = FastAPI(
    title="Sprintline Issue Tracker API",
    description="Issues, sprints, burndown, comments, activity and roadmap for the shared Sprintline workspace.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Retry-After", "X-Total-Count"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": STATUS_CODES.get(exc.status_code, "error"),
                "message": detail,
            }
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part not in ("body", "query", "path")]
        field = ".".join(location) or "body"
        fields.setdefault(field, error.get("msg", "Invalid value"))
    message = next(iter(fields.values()), "The request could not be validated")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "validation_error", "message": message, "fields": fields}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled error: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "Something went wrong on our side."}},
    )


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Liveness probe that also confirms the datastore answers."""
    database = "ok"
    try:
        with SessionLocal() as session:
            session.execute(select(func.count()).select_from(User))
    except Exception:  # noqa: BLE001 - health must report, not crash
        logger.exception("health check: datastore unreachable")
        database = "error"
    return {"status": "ok" if database == "ok" else "degraded", "database": database, "service": "sprintline-api"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing() -> HTMLResponse:
    """Human page on the API origin with live workspace counts."""
    counts = {"issues": 0, "sprints": 0, "projects": 0, "users": 0}
    try:
        with SessionLocal() as session:
            counts = {
                "issues": session.scalar(select(func.count()).select_from(Issue)) or 0,
                "sprints": session.scalar(select(func.count()).select_from(Sprint)) or 0,
                "projects": session.scalar(select(func.count()).select_from(Project)) or 0,
                "users": session.scalar(select(func.count()).select_from(User)) or 0,
            }
    except Exception:  # noqa: BLE001 - the landing page must never 500
        logger.exception("landing page: could not read workspace counts")
    return HTMLResponse(render_landing(counts))


app.include_router(auth.router)
app.include_router(meta.router)
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(activity.router)
app.include_router(sprints.router)
app.include_router(roadmap.router)
