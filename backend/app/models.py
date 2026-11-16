"""ORM models for the Sprintline shared workspace."""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    """Naive UTC timestamp — SQLite has no timezone type, so we store UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IssueStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"


class IssuePriority(str, enum.Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class SprintStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"


class ActivityKind(str, enum.Enum):
    created = "created"
    status_changed = "status_changed"
    priority_changed = "priority_changed"
    assignee_changed = "assignee_changed"
    sprint_changed = "sprint_changed"
    comment_added = "comment_added"


STATUS_VALUES = [member.value for member in IssueStatus]
PRIORITY_VALUES = [member.value for member in IssuePriority]
SPRINT_STATUS_VALUES = [member.value for member in SprintStatus]
ACTIVITY_KIND_VALUES = [member.value for member in ActivityKind]


def _pg_enum(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """Portable enum column: VARCHAR + CHECK constraint, stores the value."""
    return SAEnum(
        py_enum,
        name=name,
        native_enum=False,
        length=32,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


issue_labels = Table(
    "issue_labels",
    Base.metadata,
    Column("issue_id", ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_color: Mapped[str] = mapped_column(String(16), nullable=False, default="#9884f3")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    assigned_issues: Mapped[list["Issue"]] = relationship(
        back_populates="assignee", foreign_keys="Issue.assignee_id"
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    activities: Mapped[list["ActivityEvent"]] = relationship(back_populates="actor")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#9884f3")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    issues: Mapped[list["Issue"]] = relationship(back_populates="project")
    sprints: Mapped[list["Sprint"]] = relationship(back_populates="project")


class Sprint(Base):
    __tablename__ = "sprints"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_sprint_project_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SprintStatus] = mapped_column(_pg_enum(SprintStatus, "sprint_status"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="sprints")
    issues: Mapped[list["Issue"]] = relationship(back_populates="sprint")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(24), unique=True, nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    sprint_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sprints.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[IssueStatus] = mapped_column(
        _pg_enum(IssueStatus, "issue_status"), nullable=False, default=IssueStatus.backlog, index=True
    )
    priority: Mapped[IssuePriority] = mapped_column(
        _pg_enum(IssuePriority, "issue_priority"), nullable=False, default=IssuePriority.medium
    )
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project: Mapped[Project] = relationship(back_populates="issues")
    sprint: Mapped[Optional[Sprint]] = relationship(back_populates="issues")
    assignee: Mapped[Optional[User]] = relationship(
        back_populates="assigned_issues", foreign_keys=[assignee_id]
    )
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id])
    labels: Mapped[list["Label"]] = relationship(secondary=issue_labels, back_populates="issues")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    activities: Mapped[list["ActivityEvent"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )

    @property
    def comment_count(self) -> int:
        return len(self.comments)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#9d9da6")

    issues: Mapped[list[Issue]] = relationship(secondary=issue_labels, back_populates="labels")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    kind: Mapped[ActivityKind] = mapped_column(_pg_enum(ActivityKind, "activity_kind"), nullable=False)
    field: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    from_value: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    to_value: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, index=True)

    issue: Mapped[Issue] = relationship(back_populates="activities")
    actor: Mapped[User] = relationship(back_populates="activities")
