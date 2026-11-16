"""Append-only activity history: per issue and workspace-wide."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.deps import CurrentUser, DbSession
from app.models import ActivityEvent
from app.routers.issues import load_issue
from app.schemas import ActivityListOut, ActivityOut

router = APIRouter(prefix="/api", tags=["activity"])


def _payload(event: ActivityEvent) -> dict:
    return {
        "id": event.id,
        "issue_id": event.issue_id,
        "issue_key": event.issue.key,
        "issue_title": event.issue.title,
        "kind": event.kind,
        "field": event.field,
        "from_value": event.from_value,
        "to_value": event.to_value,
        "actor": event.actor,
        "created_at": event.created_at,
    }


def _fetch(session: Session, *, issue_id: int | None, limit: int, offset: int) -> ActivityListOut:
    conditions = [ActivityEvent.issue_id == issue_id] if issue_id is not None else []
    total = session.scalar(select(func.count()).select_from(ActivityEvent).where(*conditions)) or 0
    events = session.scalars(
        select(ActivityEvent)
        .where(*conditions)
        .options(selectinload(ActivityEvent.actor), selectinload(ActivityEvent.issue))
        .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return ActivityListOut(items=[ActivityOut.model_validate(_payload(event)) for event in events], total=total)


@router.get("/issues/{issue_id}/activity", response_model=ActivityListOut)
def issue_activity(
    issue_id: int,
    session: DbSession,
    _user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ActivityListOut:
    """The issue's history, newest first, with actor and change description."""
    load_issue(session, issue_id)
    return _fetch(session, issue_id=issue_id, limit=limit, offset=offset)


@router.get("/activity", response_model=ActivityListOut)
def workspace_activity(
    session: DbSession,
    _user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ActivityListOut:
    """Most recent events across the shared workspace (dashboard feed)."""
    return _fetch(session, issue_id=None, limit=limit, offset=offset)
