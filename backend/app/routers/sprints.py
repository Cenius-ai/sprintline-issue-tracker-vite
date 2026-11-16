"""Sprints API with derived burndown series.

The sprint list accepts ``limit``/``offset`` and reports the unpaginated total in
``X-Total-Count``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession, not_found
from app.models import IssueStatus, Sprint, SprintStatus
from app.schemas import BurndownOut, SprintOut
from app.services.burndown import build_burndown

router = APIRouter(prefix="/api/sprints", tags=["sprints"])

DEFAULT_LIMIT = 100
MAX_LIMIT = 200


def _sprint_payload(sprint: Sprint) -> SprintOut:
    issues = sprint.issues
    return SprintOut(
        id=sprint.id,
        project_id=sprint.project_id,
        project_key=sprint.project.key,
        project_name=sprint.project.name,
        name=sprint.name,
        goal=sprint.goal,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        status=sprint.status,
        issue_count=len(issues),
        point_count=sum(max(issue.estimate or 0, 0) for issue in issues),
        done_count=sum(1 for issue in issues if issue.status == IssueStatus.done),
    )


@router.get("", response_model=list[SprintOut])
def list_sprints(
    session: DbSession,
    _user: CurrentUser,
    response: Response,
    project_id: Annotated[int | None, Query()] = None,
    sprint_status: Annotated[SprintStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SprintOut]:
    """Sprints with status, date range and issue/point totals."""
    conditions = []
    if project_id is not None:
        conditions.append(Sprint.project_id == project_id)
    if sprint_status is not None:
        conditions.append(Sprint.status == sprint_status)

    total = session.scalar(select(func.count()).select_from(Sprint).where(*conditions)) or 0
    sprints = session.scalars(
        select(Sprint)
        .where(*conditions)
        .options(selectinload(Sprint.issues), selectinload(Sprint.project))
        .order_by(Sprint.start_date.desc(), Sprint.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    response.headers["X-Total-Count"] = str(total)
    return [_sprint_payload(sprint) for sprint in sprints]


@router.get("/{sprint_id}", response_model=SprintOut)
def get_sprint(sprint_id: int, session: DbSession, _user: CurrentUser) -> SprintOut:
    sprint = session.scalar(
        select(Sprint)
        .where(Sprint.id == sprint_id)
        .options(selectinload(Sprint.issues), selectinload(Sprint.project))
    )
    if sprint is None:
        raise not_found("Sprint not found")
    return _sprint_payload(sprint)


@router.get("/{sprint_id}/burndown", response_model=BurndownOut)
def sprint_burndown(sprint_id: int, session: DbSession, _user: CurrentUser) -> BurndownOut:
    """Daily ideal and actual remaining points for the sprint window."""
    sprint = session.get(Sprint, sprint_id)
    if sprint is None:
        raise not_found("Sprint not found")
    return BurndownOut.model_validate(build_burndown(session, sprint))
