"""Issues API: filtered list, create, detail, patch, delete + activity."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.deps import CurrentUser, DbSession, not_found
from app.models import (
    ActivityKind,
    Issue,
    IssuePriority,
    IssueStatus,
    Label,
    Project,
    Sprint,
    User,
    utcnow,
)
from app.schemas import IssueCreate, IssueListOut, IssueOut, IssueUpdate
from app.services import activity as activity_service

router = APIRouter(prefix="/api/issues", tags=["issues"])

ISSUE_LOAD_OPTIONS = (
    selectinload(Issue.project),
    selectinload(Issue.sprint),
    selectinload(Issue.assignee),
    selectinload(Issue.created_by),
    selectinload(Issue.labels),
    selectinload(Issue.comments),
)


def load_issue(session: Session, issue_id: int) -> Issue:
    issue = session.scalar(select(Issue).where(Issue.id == issue_id).options(*ISSUE_LOAD_OPTIONS))
    if issue is None:
        raise not_found("Issue not found")
    return issue


def _next_issue_key(session: Session, project: Project) -> str:
    keys = session.scalars(select(Issue.key).where(Issue.project_id == project.id)).all()
    highest = 0
    for key in keys:
        suffix = key.rsplit("-", 1)[-1]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{project.key}-{highest + 1}"


def _resolve_project(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=422, detail="Unknown project")
    return project


def _resolve_sprint(session: Session, sprint_id: int | None, project_id: int) -> Sprint | None:
    if sprint_id is None:
        return None
    sprint = session.get(Sprint, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=422, detail="Unknown sprint")
    if sprint.project_id != project_id:
        raise HTTPException(status_code=422, detail="Sprint belongs to another project")
    return sprint


def _resolve_assignee(session: Session, assignee_id: int | None) -> User | None:
    if assignee_id is None:
        return None
    assignee = session.get(User, assignee_id)
    if assignee is None:
        raise HTTPException(status_code=422, detail="Unknown assignee")
    return assignee


def _resolve_labels(session: Session, label_ids: list[int]) -> list[Label]:
    if not label_ids:
        return []
    labels = list(session.scalars(select(Label).where(Label.id.in_(label_ids))))
    if len(labels) != len(set(label_ids)):
        raise HTTPException(status_code=422, detail="Unknown label")
    return labels


@router.get("", response_model=IssueListOut)
def list_issues(
    session: DbSession,
    _user: CurrentUser,
    issue_status: Annotated[list[IssueStatus] | None, Query(alias="status")] = None,
    priority: Annotated[list[IssuePriority] | None, Query()] = None,
    assignee_id: Annotated[str | None, Query()] = None,
    label_id: Annotated[int | None, Query()] = None,
    sprint_id: Annotated[int | None, Query()] = None,
    project_id: Annotated[int | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> IssueListOut:
    """List issues. ``assignee_id=unassigned`` filters issues with no assignee."""
    conditions = []
    if issue_status:
        conditions.append(Issue.status.in_(issue_status))
    if priority:
        conditions.append(Issue.priority.in_(priority))
    if assignee_id:
        if assignee_id == "unassigned":
            conditions.append(Issue.assignee_id.is_(None))
        elif assignee_id.isdigit():
            conditions.append(Issue.assignee_id == int(assignee_id))
    if sprint_id is not None:
        conditions.append(Issue.sprint_id == sprint_id)
    if project_id is not None:
        conditions.append(Issue.project_id == project_id)
    if label_id is not None:
        conditions.append(Issue.labels.any(Label.id == label_id))
    if q:
        needle = f"%{q.strip()}%"
        conditions.append(
            or_(
                Issue.title.ilike(needle),
                Issue.description.ilike(needle),
                Issue.key.ilike(needle),
            )
        )

    total = session.scalar(select(func.count()).select_from(Issue).where(*conditions)) or 0
    rows = session.scalars(
        select(Issue)
        .where(*conditions)
        .options(*ISSUE_LOAD_OPTIONS)
        .order_by(Issue.created_at.desc(), Issue.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return IssueListOut(
        items=[IssueOut.model_validate(issue) for issue in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, session: DbSession, user: CurrentUser) -> IssueOut:
    """Create an issue, generate its key and record a ``created`` activity event."""
    project = _resolve_project(session, payload.project_id)
    sprint = _resolve_sprint(session, payload.sprint_id, project.id)
    assignee = _resolve_assignee(session, payload.assignee_id)
    labels = _resolve_labels(session, payload.label_ids)

    now = utcnow()
    issue = Issue(
        key=_next_issue_key(session, project),
        project_id=project.id,
        sprint_id=sprint.id if sprint else None,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee_id=assignee.id if assignee else None,
        estimate=payload.estimate,
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
        completed_at=now if payload.status == IssueStatus.done else None,
    )
    issue.labels = labels
    session.add(issue)
    session.flush()

    activity_service.record(session, issue, user, ActivityKind.created, created_at=now)
    if payload.status == IssueStatus.done:
        activity_service.record(
            session,
            issue,
            user,
            ActivityKind.status_changed,
            field="status",
            from_value=IssueStatus.backlog.value,
            to_value=IssueStatus.done.value,
            created_at=now,
        )
    session.commit()
    return IssueOut.model_validate(load_issue(session, issue.id))


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, session: DbSession, _user: CurrentUser) -> IssueOut:
    return IssueOut.model_validate(load_issue(session, issue_id))


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, payload: IssueUpdate, session: DbSession, user: CurrentUser) -> IssueOut:
    """Partially update an issue and record activity for every tracked change."""
    issue = load_issue(session, issue_id)
    changes = payload.model_dump(exclude_unset=True)
    now = utcnow()

    if "title" in changes and changes["title"] != issue.title:
        issue.title = changes["title"]
    if "description" in changes and changes["description"] != issue.description:
        issue.description = changes["description"]
    if "estimate" in changes and changes["estimate"] != issue.estimate:
        issue.estimate = changes["estimate"]

    if "priority" in changes and changes["priority"] != issue.priority:
        previous = issue.priority
        issue.priority = changes["priority"]
        activity_service.record(
            session,
            issue,
            user,
            ActivityKind.priority_changed,
            field="priority",
            from_value=previous.value,
            to_value=issue.priority.value,
            created_at=now,
        )

    if "status" in changes and changes["status"] != issue.status:
        previous = issue.status
        issue.status = changes["status"]
        if issue.status == IssueStatus.done:
            issue.completed_at = now
        elif previous == IssueStatus.done:
            issue.completed_at = None
        activity_service.record(
            session,
            issue,
            user,
            ActivityKind.status_changed,
            field="status",
            from_value=previous.value,
            to_value=issue.status.value,
            created_at=now,
        )

    if "assignee_id" in changes:
        new_assignee = _resolve_assignee(session, changes["assignee_id"])
        new_assignee_id = new_assignee.id if new_assignee else None
        if new_assignee_id != issue.assignee_id:
            previous_name = issue.assignee.name if issue.assignee else "Unassigned"
            issue.assignee = new_assignee
            activity_service.record(
                session,
                issue,
                user,
                ActivityKind.assignee_changed,
                field="assignee",
                from_value=previous_name,
                to_value=new_assignee.name if new_assignee else "Unassigned",
                created_at=now,
            )

    if "sprint_id" in changes:
        new_sprint = _resolve_sprint(session, changes["sprint_id"], issue.project_id)
        new_sprint_id = new_sprint.id if new_sprint else None
        if new_sprint_id != issue.sprint_id:
            previous_name = issue.sprint.name if issue.sprint else "Backlog"
            issue.sprint = new_sprint
            activity_service.record(
                session,
                issue,
                user,
                ActivityKind.sprint_changed,
                field="sprint",
                from_value=previous_name,
                to_value=new_sprint.name if new_sprint else "Backlog",
                created_at=now,
            )

    if "label_ids" in changes and changes["label_ids"] is not None:
        issue.labels = _resolve_labels(session, changes["label_ids"])

    issue.updated_at = now
    session.commit()
    return IssueOut.model_validate(load_issue(session, issue_id))


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, session: DbSession, _user: CurrentUser) -> Response:
    """Delete an issue together with its comments, activity and label links."""
    issue = load_issue(session, issue_id)
    session.delete(issue)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
