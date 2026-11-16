"""Roadmap endpoint: projects grouped into Now / Next / Later / Done.

Lanes are derived on read from persisted sprint status and issue state (no
duplicated roadmap table).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.models import Issue, IssuePriority, IssueStatus, Project, SprintStatus
from app.schemas import RoadmapCard, RoadmapLanes, RoadmapOut, RoadmapProject

router = APIRouter(prefix="/api", tags=["roadmap"])

LANE_ORDER = ["now", "next", "later", "done"]
PRIORITY_RANK = {
    IssuePriority.urgent: 0,
    IssuePriority.high: 1,
    IssuePriority.medium: 2,
    IssuePriority.low: 3,
    IssuePriority.none: 4,
}


def _lane_for(issue: Issue) -> str:
    if issue.status == IssueStatus.done:
        return "done"
    if issue.sprint is not None and issue.sprint.status == SprintStatus.active:
        return "now"
    if issue.sprint is not None and issue.sprint.status == SprintStatus.planned:
        return "next"
    return "later"


@router.get("/roadmap", response_model=RoadmapOut)
def get_roadmap(
    session: DbSession,
    _user: CurrentUser,
    project_id: Annotated[int | None, Query()] = None,
) -> RoadmapOut:
    """Each project with four lanes derived from live sprint and issue state."""
    conditions = [Project.id == project_id] if project_id is not None else []
    projects = session.scalars(select(Project).where(*conditions).order_by(Project.key)).all()

    rows: list[RoadmapProject] = []
    for project in projects:
        issues = session.scalars(
            select(Issue)
            .where(Issue.project_id == project.id)
            .options(selectinload(Issue.sprint), selectinload(Issue.assignee))
        ).all()
        buckets: dict[str, list[Issue]] = {lane: [] for lane in LANE_ORDER}
        for issue in issues:
            buckets[_lane_for(issue)].append(issue)

        lanes = {}
        counts = {}
        for lane in LANE_ORDER:
            ordered = sorted(buckets[lane], key=lambda item: (PRIORITY_RANK[item.priority], item.key))
            lanes[lane] = [RoadmapCard.model_validate(issue) for issue in ordered]
            counts[lane] = len(ordered)

        rows.append(
            RoadmapProject(
                project=project,
                lanes=RoadmapLanes(**lanes),
                counts=counts,
            )
        )

    return RoadmapOut(lanes=LANE_ORDER, projects=rows)
