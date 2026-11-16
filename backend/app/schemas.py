"""Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from app.models import ActivityKind, IssuePriority, IssueStatus, SprintStatus


def iso_utc(value: datetime | None) -> str | None:
    """Serialize naive-UTC datetimes as explicit UTC ISO strings."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", "completed_at", check_fields=False, when_used="json")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return iso_utc(value)


# --------------------------------------------------------------------------- #
# Read models
# --------------------------------------------------------------------------- #
class UserOut(ApiModel):
    id: int
    email: EmailStr
    name: str
    avatar_color: str


class ProjectOut(ApiModel):
    id: int
    key: str
    name: str
    description: str
    color: str


class LabelOut(ApiModel):
    id: int
    name: str
    color: str


class SprintRef(ApiModel):
    id: int
    name: str
    status: SprintStatus


class SprintOut(ApiModel):
    id: int
    project_id: int
    project_key: str
    project_name: str
    name: str
    goal: str
    start_date: date
    end_date: date
    status: SprintStatus
    issue_count: int
    point_count: int
    done_count: int

    @field_serializer("start_date", "end_date", when_used="json")
    def _serialize_date(self, value: date) -> str:
        return value.isoformat()


class IssueOut(ApiModel):
    id: int
    key: str
    title: str
    description: str
    status: IssueStatus
    priority: IssuePriority
    estimate: int
    project: ProjectOut
    sprint: Optional[SprintRef]
    assignee: Optional[UserOut]
    created_by: Optional[UserOut]
    labels: list[LabelOut]
    comment_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class IssueListOut(BaseModel):
    items: list[IssueOut]
    total: int
    limit: int
    offset: int


class CommentOut(ApiModel):
    id: int
    issue_id: int
    body: str
    author: UserOut
    created_at: datetime


class ActivityOut(ApiModel):
    id: int
    issue_id: int
    issue_key: str
    issue_title: str
    kind: ActivityKind
    field: Optional[str]
    from_value: Optional[str]
    to_value: Optional[str]
    actor: UserOut
    created_at: datetime


class ActivityListOut(BaseModel):
    items: list[ActivityOut]
    total: int


class BurndownPoint(BaseModel):
    date: str
    ideal: float
    actual: float


class BurndownOut(BaseModel):
    sprint_id: int
    sprint_name: str
    sprint_status: SprintStatus
    start_date: str
    end_date: str
    total_points: float
    completed_points: float
    days: int
    points: list[BurndownPoint]


class RoadmapCard(ApiModel):
    id: int
    key: str
    title: str
    status: IssueStatus
    priority: IssuePriority
    estimate: int
    assignee: Optional[UserOut]


class RoadmapLanes(BaseModel):
    now: list[RoadmapCard]
    next: list[RoadmapCard]
    later: list[RoadmapCard]
    done: list[RoadmapCard]


class RoadmapProject(BaseModel):
    project: ProjectOut
    lanes: RoadmapLanes
    counts: dict[str, int]


class RoadmapOut(BaseModel):
    lanes: list[str]
    projects: list[RoadmapProject]


# --------------------------------------------------------------------------- #
# Write models
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_at: str
    user: UserOut


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=8000)
    status: IssueStatus = IssueStatus.backlog
    priority: IssuePriority = IssuePriority.medium
    project_id: int
    sprint_id: Optional[int] = None
    assignee_id: Optional[int] = None
    estimate: int = Field(default=0, ge=0, le=100)
    label_ids: list[int] = Field(default_factory=list, max_length=20)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title is required")
        return cleaned

    @field_validator("description")
    @classmethod
    def _trim_description(cls, value: str) -> str:
        return value.strip()


class IssueUpdate(BaseModel):
    """Partial update. Only fields present in the request body are applied."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=8000)
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    sprint_id: Optional[int] = None
    assignee_id: Optional[int] = None
    estimate: Optional[int] = Field(default=None, ge=0, le=100)
    label_ids: Optional[list[int]] = Field(default=None, max_length=20)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title is required")
        return cleaned

    @field_validator("description")
    @classmethod
    def _trim_description(cls, value: str | None) -> str | None:
        return None if value is None else value.strip()


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)

    @field_validator("body")
    @classmethod
    def _body_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Comment cannot be empty")
        return cleaned
