"""Workspace reference data: projects, users, labels.

Every list endpoint accepts ``limit``/``offset`` and reports the unpaginated
total in ``X-Total-Count`` so clients can page without a body-shape change.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Label, Project, User
from app.schemas import LabelOut, ProjectOut, UserOut

router = APIRouter(prefix="/api", tags=["workspace"])

DEFAULT_LIMIT = 100
MAX_LIMIT = 200


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    session: DbSession,
    _user: CurrentUser,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectOut]:
    total = session.scalar(select(func.count()).select_from(Project)) or 0
    projects = session.scalars(
        select(Project).order_by(Project.id).limit(limit).offset(offset)
    ).all()
    response.headers["X-Total-Count"] = str(total)
    return [ProjectOut.model_validate(project) for project in projects]


@router.get("/users", response_model=list[UserOut])
def list_users(
    session: DbSession,
    _user: CurrentUser,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserOut]:
    total = session.scalar(select(func.count()).select_from(User)) or 0
    users = session.scalars(select(User).order_by(User.name).limit(limit).offset(offset)).all()
    response.headers["X-Total-Count"] = str(total)
    return [UserOut.model_validate(user) for user in users]


@router.get("/labels", response_model=list[LabelOut])
def list_labels(
    session: DbSession,
    _user: CurrentUser,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LabelOut]:
    total = session.scalar(select(func.count()).select_from(Label)) or 0
    labels = session.scalars(select(Label).order_by(Label.name).limit(limit).offset(offset)).all()
    response.headers["X-Total-Count"] = str(total)
    return [LabelOut.model_validate(label) for label in labels]
