"""Issue comments: oldest-first stream with author names.

The stream accepts ``limit``/``offset`` and reports the full comment count in
``X-Total-Count``; the issue's ``comment_count`` field always reflects the total.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.models import ActivityKind, Comment, Issue
from app.routers.issues import load_issue
from app.schemas import CommentCreate, CommentOut
from app.services import activity as activity_service

router = APIRouter(prefix="/api/issues/{issue_id}/comments", tags=["comments"])

DEFAULT_LIMIT = 100
MAX_LIMIT = 200


@router.get("", response_model=list[CommentOut])
def list_comments(
    issue_id: int,
    session: DbSession,
    _user: CurrentUser,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CommentOut]:
    """Comments for an issue, oldest first, with author names."""
    load_issue(session, issue_id)
    total = (
        session.scalar(select(func.count()).select_from(Comment).where(Comment.issue_id == issue_id)) or 0
    )
    comments = session.scalars(
        select(Comment)
        .where(Comment.issue_id == issue_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    response.headers["X-Total-Count"] = str(total)
    return [CommentOut.model_validate(comment) for comment in comments]


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(issue_id: int, payload: CommentCreate, session: DbSession, user: CurrentUser) -> CommentOut:
    """Append a comment and record a ``comment_added`` activity event."""
    issue: Issue = load_issue(session, issue_id)
    comment = Comment(issue_id=issue.id, author_id=user.id, body=payload.body)
    session.add(comment)
    session.flush()
    activity_service.record(session, issue, user, ActivityKind.comment_added, created_at=comment.created_at)
    session.commit()
    session.refresh(comment)
    return CommentOut.model_validate(comment)
