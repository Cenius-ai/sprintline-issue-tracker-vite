"""Burndown series derived from persisted issue completion timestamps."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Issue, Sprint, utcnow


def _today() -> date:
    return utcnow().date()


def build_burndown(session: Session, sprint: Sprint) -> dict:
    """Daily ideal vs actual remaining points for the sprint window.

    * ``ideal`` burns linearly from the total to zero across the window.
    * ``actual`` is ``total - points completed on or before that day``, using the
      persisted ``completed_at`` timestamps. Days after today hold the current
      remaining value so a planned or in-flight sprint still draws a real line.
    """
    issues = list(session.scalars(select(Issue).where(Issue.sprint_id == sprint.id)))
    points_by_issue = {issue.id: max(issue.estimate or 0, 0) for issue in issues}
    total_points = float(sum(points_by_issue.values()))
    completed_points = float(
        sum(points_by_issue[issue.id] for issue in issues if issue.completed_at is not None)
    )

    span_days = (sprint.end_date - sprint.start_date).days + 1
    span_days = max(span_days, 1)
    denominator = max(span_days - 1, 1)
    today = _today()

    series: list[dict] = []
    for offset in range(span_days):
        day = sprint.start_date + timedelta(days=offset)
        ideal = round(total_points * (1 - offset / denominator), 2)
        cutoff = min(day, today)
        burned = 0
        for issue in issues:
            if issue.completed_at is not None and issue.completed_at.date() <= cutoff:
                burned += points_by_issue[issue.id]
        series.append(
            {
                "date": day.isoformat(),
                "ideal": max(ideal, 0.0),
                "actual": float(max(total_points - burned, 0)),
            }
        )

    return {
        "sprint_id": sprint.id,
        "sprint_name": sprint.name,
        "sprint_status": sprint.status,
        "start_date": sprint.start_date.isoformat(),
        "end_date": sprint.end_date.isoformat(),
        "total_points": total_points,
        "completed_points": completed_points,
        "days": span_days,
        "points": series,
    }
