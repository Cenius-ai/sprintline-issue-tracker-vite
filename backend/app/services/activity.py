"""Append-only activity log helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import ActivityEvent, ActivityKind, Issue, User, utcnow


def record(
    session: Session,
    issue: Issue,
    actor: User,
    kind: ActivityKind,
    *,
    field: str | None = None,
    from_value: str | None = None,
    to_value: str | None = None,
    created_at: datetime | None = None,
) -> ActivityEvent:
    """Append one immutable activity row. Never mutates an existing row."""
    event = ActivityEvent(
        issue_id=issue.id,
        actor_id=actor.id,
        kind=kind,
        field=field,
        from_value=from_value,
        to_value=to_value,
        created_at=created_at or utcnow(),
    )
    session.add(event)
    return event


def describe(event: ActivityEvent) -> str:
    """Human-readable one-liner used by the client and by tests."""
    kind = event.kind.value if isinstance(event.kind, ActivityKind) else str(event.kind)
    field = event.field or "field"
    if kind == "created":
        return "created this issue"
    if kind == "comment_added":
        return "commented"
    if kind.endswith("_changed"):
        before = event.from_value or "none"
        after = event.to_value or "none"
        if field == "status":
            return f"changed status from {before} to {after}"
        if field == "priority":
            return f"changed priority from {before} to {after}"
        if field == "assignee":
            return f"reassigned from {before} to {after}"
        if field == "sprint":
            return f"moved sprint from {before} to {after}"
        return f"changed {field} from {before} to {after}"
    return f"updated {field}"
