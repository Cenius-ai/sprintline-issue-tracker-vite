"""Deterministic, idempotent seed for the shared Sprintline demo workspace.

Content: 4 users (the demo login plus three teammates), 2 projects, 3 sprint
cycles, 24 issues across statuses/priorities/labels/sprints, 11 comments and a
complete activity history. Safe to re-run: an already-seeded database is left
untouched, and every insert is guarded by a natural key.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ActivityEvent,
    ActivityKind,
    Comment,
    Issue,
    IssuePriority,
    IssueStatus,
    Label,
    Project,
    Sprint,
    SprintStatus,
    User,
    utcnow,
)
from app.security import hash_password

DEMO_EMAIL = "cenius@cenius.ai"
DEMO_PASSWORD = "cenius"

USERS = [
    {"email": DEMO_EMAIL, "name": "Cenius Demo", "avatar_color": "#9884f3"},
    {"email": "maya.okafor@cenius.ai", "name": "Maya Okafor", "avatar_color": "#5fd08a"},
    {"email": "diego.marin@cenius.ai", "name": "Diego Marín", "avatar_color": "#f3b562"},
    {"email": "priya.raman@cenius.ai", "name": "Priya Raman", "avatar_color": "#7dd3fc"},
]

PROJECTS = [
    {
        "key": "SPL",
        "name": "Sprintline Web App",
        "color": "#9884f3",
        "description": "The browser client teams use every day: issue list, sprint board, roadmap and workspace overview.",
    },
    {
        "key": "MOB",
        "name": "Sprintline Mobile",
        "color": "#5fd08a",
        "description": "Companion app for on-call engineers: offline cache, push notifications and biometric unlock.",
    },
]

LABELS = [
    {"name": "bug", "color": "#f87171"},
    {"name": "feature", "color": "#a78bfa"},
    {"name": "design", "color": "#c3a6ff"},
    {"name": "performance", "color": "#fbbf24"},
    {"name": "infra", "color": "#7dd3fc"},
    {"name": "docs", "color": "#9d9da6"},
]

SPRINTS = [
    {
        "project": "SPL",
        "name": "Sprint 12 — Issue core",
        "goal": "Ship create/edit, the filter bar and issue key generation for the first paying team.",
        "start_offset": -21,
        "end_offset": -8,
        "status": SprintStatus.completed,
    },
    {
        "project": "SPL",
        "name": "Sprint 13 — Collaboration",
        "goal": "Comments, activity history and a sprint board that survives real sprint load.",
        "start_offset": -5,
        "end_offset": 9,
        "status": SprintStatus.active,
    },
    {
        "project": "SPL",
        "name": "Sprint 14 — Roadmap & reporting",
        "goal": "Roadmap lanes, an honest burndown and roadmap documentation for self-hosters.",
        "start_offset": 10,
        "end_offset": 24,
        "status": SprintStatus.planned,
    },
]

# offset days are relative to the seed run; completed offsets drive the burndown.
ISSUES = [
    # ---- Sprint 12 (completed) -------------------------------------------- #
    {
        "key": "SPL-1",
        "project": "SPL",
        "sprint": "Sprint 12 — Issue core",
        "title": "Create issue form with required-title validation",
        "description": "A first-time user must be able to file an issue in under a minute. Title is required, everything else has a sensible default.",
        "status": IssueStatus.done,
        "priority": IssuePriority.medium,
        "assignee": "Maya Okafor",
        "creator": "Cenius Demo",
        "estimate": 3,
        "labels": ["feature"],
        "created_offset": 30,
        "completed_offset": 16,
    },
    {
        "key": "SPL-2",
        "project": "SPL",
        "sprint": "Sprint 12 — Issue core",
        "title": "Issue keys collide after deleting the newest issue",
        "description": "Deleting the highest issue and creating a new one reuses the deleted key, which trips the unique constraint on issues.key.",
        "status": IssueStatus.done,
        "priority": IssuePriority.high,
        "assignee": "Diego Marín",
        "creator": "Maya Okafor",
        "estimate": 2,
        "labels": ["bug"],
        "created_offset": 28,
        "completed_offset": 14,
        "history": [
            ("priority_changed", "priority", "medium", "high", 17),
            ("status_changed", "status", "todo", "in_progress", 16),
        ],
    },
    {
        "key": "SPL-3",
        "project": "SPL",
        "sprint": "Sprint 12 — Issue core",
        "title": "Filter bar overflows on 375px viewports",
        "description": "The filter selects sit in a single row and push the search box off screen on small phones.",
        "status": IssueStatus.done,
        "priority": IssuePriority.medium,
        "assignee": "Priya Raman",
        "creator": "Priya Raman",
        "estimate": 2,
        "labels": ["bug", "design"],
        "created_offset": 27,
        "completed_offset": 13,
        "history": [("priority_changed", "priority", "low", "medium", 20)],
    },
    {
        "key": "SPL-4",
        "project": "SPL",
        "sprint": "Sprint 12 — Issue core",
        "title": "Add estimate points to the issue model",
        "description": "Point estimates are the input to the burndown, so they belong on the issue rather than in a separate planning sheet.",
        "status": IssueStatus.done,
        "priority": IssuePriority.low,
        "assignee": "Maya Okafor",
        "creator": "Cenius Demo",
        "estimate": 1,
        "labels": ["feature"],
        "created_offset": 26,
        "completed_offset": 11,
    },
    {
        "key": "SPL-5",
        "project": "SPL",
        "sprint": "Sprint 12 — Issue core",
        "title": "Search ignores issue keys",
        "description": "Typing SPL-12 into the search box returns nothing because only titles and descriptions are matched.",
        "status": IssueStatus.done,
        "priority": IssuePriority.high,
        "assignee": "Diego Marín",
        "creator": "Diego Marín",
        "estimate": 2,
        "labels": ["bug"],
        "created_offset": 25,
        "completed_offset": 9,
    },
    {
        "key": "SPL-6",
        "project": "SPL",
        "sprint": None,
        "title": "Bulk import issues from CSV",
        "description": "Teams migrating from another tracker want to paste a CSV export and map columns instead of retyping 400 rows.",
        "status": IssueStatus.todo,
        "priority": IssuePriority.low,
        "assignee": None,
        "creator": "Cenius Demo",
        "estimate": 5,
        "labels": ["feature"],
        "created_offset": 24,
        "history": [("sprint_changed", "sprint", "Sprint 12 — Issue core", "Backlog", 7)],
    },
    # ---- Sprint 13 (active) ----------------------------------------------- #
    {
        "key": "SPL-7",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Comment composer loses text when the session refreshes",
        "description": "A comment typed while the token silently refreshes is dropped from the box and never posted.",
        "status": IssueStatus.in_progress,
        "priority": IssuePriority.high,
        "assignee": "Maya Okafor",
        "creator": "Priya Raman",
        "estimate": 3,
        "labels": ["bug"],
        "created_offset": 12,
        "history": [
            ("priority_changed", "priority", "medium", "high", 9),
            ("status_changed", "status", "todo", "in_progress", 8),
        ],
    },
    {
        "key": "SPL-8",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Record status changes in the activity feed",
        "description": "Every status move must append an immutable event with actor and timestamp so the history explains itself.",
        "status": IssueStatus.done,
        "priority": IssuePriority.high,
        "assignee": "Diego Marín",
        "creator": "Cenius Demo",
        "estimate": 3,
        "labels": ["feature"],
        "created_offset": 11,
        "completed_offset": 2,
    },
    {
        "key": "SPL-9",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Board column move persists the new status",
        "description": "Moving a card between columns has to write the new status through PATCH and survive a full reload.",
        "status": IssueStatus.in_review,
        "priority": IssuePriority.high,
        "assignee": "Cenius Demo",
        "creator": "Cenius Demo",
        "estimate": 5,
        "labels": ["feature"],
        "created_offset": 10,
        "history": [
            ("status_changed", "status", "todo", "in_progress", 8),
            ("status_changed", "status", "in_progress", "in_review", 3),
        ],
    },
    {
        "key": "SPL-10",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Burndown chart plots ideal against actual points",
        "description": "The ideal line is a straight burn from the sprint total; the actual line is recomputed from completed_at timestamps.",
        "status": IssueStatus.done,
        "priority": IssuePriority.medium,
        "assignee": "Priya Raman",
        "creator": "Priya Raman",
        "estimate": 5,
        "labels": ["feature"],
        "created_offset": 10,
        "completed_offset": 1,
    },
    {
        "key": "SPL-11",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Assignee initials render inconsistently in board cards",
        "description": "Two-letter initials and single-word names produce different avatar sizes, which breaks the card rhythm.",
        "status": IssueStatus.in_progress,
        "priority": IssuePriority.low,
        "assignee": "Priya Raman",
        "creator": "Maya Okafor",
        "estimate": 1,
        "labels": ["design"],
        "created_offset": 9,
        "history": [("status_changed", "status", "todo", "in_progress", 5)],
    },
    {
        "key": "SPL-12",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Comment timestamps drift by the viewer's timezone",
        "description": "Timestamps arrive as naive strings and are parsed as local time, so a comment posted now reads as two hours old.",
        "status": IssueStatus.in_review,
        "priority": IssuePriority.medium,
        "assignee": "Diego Marín",
        "creator": "Diego Marín",
        "estimate": 2,
        "labels": ["bug"],
        "created_offset": 8,
        "history": [("status_changed", "status", "todo", "in_review", 4)],
    },
    {
        "key": "SPL-13",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Empty board column invites adding an issue",
        "description": "An empty column currently renders as blank space. It should explain itself and offer the create form with the status pre-filled.",
        "status": IssueStatus.todo,
        "priority": IssuePriority.low,
        "assignee": None,
        "creator": "Maya Okafor",
        "estimate": 1,
        "labels": ["design"],
        "created_offset": 6,
    },
    {
        "key": "SPL-14",
        "project": "SPL",
        "sprint": "Sprint 13 — Collaboration",
        "title": "Board gets slow with 200 cards in one sprint",
        "description": "Every card re-renders on any status change. Needs memoised cards and a bounded column height before the next big team onboards.",
        "status": IssueStatus.backlog,
        "priority": IssuePriority.medium,
        "assignee": None,
        "creator": "Diego Marín",
        "estimate": 8,
        "labels": ["performance"],
        "created_offset": 5,
    },
    # ---- Sprint 14 (planned) ---------------------------------------------- #
    {
        "key": "SPL-15",
        "project": "SPL",
        "sprint": "Sprint 14 — Roadmap & reporting",
        "title": "Public changelog page generated from releases",
        "description": "Self-hosting teams want a changelog they can point customers at without maintaining a second document.",
        "status": IssueStatus.todo,
        "priority": IssuePriority.low,
        "assignee": None,
        "creator": "Cenius Demo",
        "estimate": 5,
        "labels": ["feature", "docs"],
        "created_offset": 18,
    },
    {
        "key": "SPL-16",
        "project": "SPL",
        "sprint": None,
        "title": "Single sign-on with Google Workspace",
        "description": "Larger teams will not manage another password. Blocked until we have a second real workspace to test against.",
        "status": IssueStatus.backlog,
        "priority": IssuePriority.medium,
        "assignee": None,
        "creator": "Cenius Demo",
        "estimate": 8,
        "labels": ["feature", "infra"],
        "created_offset": 20,
    },
    {
        "key": "SPL-17",
        "project": "SPL",
        "sprint": "Sprint 14 — Roadmap & reporting",
        "title": "Document the self-hosting guide",
        "description": "Two commands, one SQLite file and a documented demo credential. Write it down before the first external deployment.",
        "status": IssueStatus.todo,
        "priority": IssuePriority.low,
        "assignee": "Priya Raman",
        "creator": "Priya Raman",
        "estimate": 2,
        "labels": ["docs"],
        "created_offset": 7,
    },
    # ---- Mobile project --------------------------------------------------- #
    {
        "key": "MOB-1",
        "project": "MOB",
        "sprint": None,
        "title": "Offline cache for the issue list",
        "description": "On-call engineers lose signal in the office stairwell. Cache the last issue list and replay writes when the network returns.",
        "status": IssueStatus.done,
        "priority": IssuePriority.high,
        "assignee": "Diego Marín",
        "creator": "Diego Marín",
        "estimate": 5,
        "labels": ["feature"],
        "created_offset": 25,
        "completed_offset": 6,
    },
    {
        "key": "MOB-2",
        "project": "MOB",
        "sprint": None,
        "title": "Push notification opt-in screen",
        "description": "Ask for notification permission in context, after the user assigns themselves their first issue.",
        "status": IssueStatus.done,
        "priority": IssuePriority.medium,
        "assignee": "Priya Raman",
        "creator": "Priya Raman",
        "estimate": 3,
        "labels": ["feature"],
        "created_offset": 22,
        "completed_offset": 4,
    },
    {
        "key": "MOB-3",
        "project": "MOB",
        "sprint": None,
        "title": "Crash on Android when opening a board with 30+ cards",
        "description": "The board renders before the sprint payload resolves, so the card list maps over undefined. Blocks the Play Store rollout.",
        "status": IssueStatus.todo,
        "priority": IssuePriority.urgent,
        "assignee": "Diego Marín",
        "creator": "Cenius Demo",
        "estimate": 5,
        "labels": ["bug"],
        "created_offset": 9,
        "history": [("priority_changed", "priority", "medium", "urgent", 6)],
    },
    {
        "key": "MOB-4",
        "project": "MOB",
        "sprint": None,
        "title": "Dark theme matches the web palette",
        "description": "Mobile currently ships a blue-grey dark theme that clashes with the accent used everywhere else.",
        "status": IssueStatus.in_progress,
        "priority": IssuePriority.medium,
        "assignee": "Maya Okafor",
        "creator": "Maya Okafor",
        "estimate": 3,
        "labels": ["design"],
        "created_offset": 13,
    },
    {
        "key": "MOB-5",
        "project": "MOB",
        "sprint": None,
        "title": "Biometric unlock for returning users",
        "description": "Face ID and fingerprint unlock after the first sign-in, with the token kept in the platform keychain.",
        "status": IssueStatus.backlog,
        "priority": IssuePriority.low,
        "assignee": None,
        "creator": "Cenius Demo",
        "estimate": 8,
        "labels": ["feature"],
        "created_offset": 19,
    },
    {
        "key": "MOB-6",
        "project": "MOB",
        "sprint": None,
        "title": "Sync conflicts silently drop comments",
        "description": "When two clients post to the same issue offline, the later replay wins and the earlier comment disappears from the stream.",
        "status": IssueStatus.backlog,
        "priority": IssuePriority.high,
        "assignee": None,
        "creator": "Diego Marín",
        "estimate": 5,
        "labels": ["bug"],
        "created_offset": 15,
    },
    {
        "key": "MOB-7",
        "project": "MOB",
        "sprint": None,
        "title": "Refresh the App Store screenshots",
        "description": "The store listing still shows the old light theme and the pre-board navigation.",
        "status": IssueStatus.backlog,
        "priority": IssuePriority.none,
        "assignee": "Priya Raman",
        "creator": "Priya Raman",
        "estimate": 1,
        "labels": ["design"],
        "created_offset": 17,
    },
]

COMMENTS = [
    ("SPL-2", "Maya Okafor", "Reproduced: delete the newest issue, create a new one, and the create call 409s on the unique key.", 16),
    ("SPL-2", "Diego Marín", "Fixed by deriving the key from the highest existing suffix inside the transaction. Added a delete-then-create regression test.", 15),
    ("SPL-7", "Priya Raman", "This bites anyone who leaves a tab open past the token window. Keep the draft in a ref and retry once after the refresh.", 10),
    ("SPL-7", "Maya Okafor", "Draft survives the silent refresh now. The hard-expiry case still throws the text away.", 6),
    ("SPL-7", "Cenius Demo", "Let's also keep the typed text when the API returns a validation error, then ship it.", 2),
    ("SPL-9", "Diego Marín", "The status control persists through PATCH and the board refetches after the mutation, so the move survives a reload.", 7),
    ("SPL-9", "Cenius Demo", "Verified on staging: moved three cards, reloaded, all three stayed in their new columns.", 3),
    ("SPL-10", "Priya Raman", "Ideal line is dashed and actual is solid; both come from real data, no mock curve.", 5),
    ("SPL-10", "Maya Okafor", "Sprint 12 shows a real burn and ends with 5 points left because of the CSV import carry-over.", 2),
    ("SPL-13", "Maya Okafor", "The empty column should offer the same create form as the issue list, pre-filled with the column's status.", 4),
    ("MOB-3", "Diego Marín", "Stack trace from the crash report: the board renders before the sprint payload lands, so cards map over undefined.", 5),
]


def _get_or_create_user(session: Session, email: str, name: str, avatar_color: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(DEMO_PASSWORD),
        avatar_color=avatar_color,
        created_at=utcnow() - timedelta(days=120),
    )
    session.add(user)
    session.flush()
    return user


def _run_seed(session: Session) -> dict:
    now = utcnow()
    today = now.date()

    users: dict[str, User] = {}
    for spec in USERS:
        users[spec["name"]] = _get_or_create_user(session, spec["email"], spec["name"], spec["avatar_color"])

    projects: dict[str, Project] = {}
    for spec in PROJECTS:
        project = session.scalar(select(Project).where(Project.key == spec["key"]))
        if project is None:
            project = Project(
                key=spec["key"],
                name=spec["name"],
                description=spec["description"],
                color=spec["color"],
                created_at=now - timedelta(days=110),
            )
            session.add(project)
            session.flush()
        projects[spec["key"]] = project

    labels: dict[str, Label] = {}
    for spec in LABELS:
        label = session.scalar(select(Label).where(Label.name == spec["name"]))
        if label is None:
            label = Label(name=spec["name"], color=spec["color"])
            session.add(label)
            session.flush()
        labels[spec["name"]] = label

    sprints: dict[str, Sprint] = {}
    for spec in SPRINTS:
        project = projects[spec["project"]]
        sprint = session.scalar(
            select(Sprint).where(Sprint.project_id == project.id, Sprint.name == spec["name"])
        )
        if sprint is None:
            sprint = Sprint(
                project_id=project.id,
                name=spec["name"],
                goal=spec["goal"],
                start_date=today + timedelta(days=spec["start_offset"]),
                end_date=today + timedelta(days=spec["end_offset"]),
                status=spec["status"],
            )
            session.add(sprint)
            session.flush()
        sprints[spec["name"]] = sprint

    issues: dict[str, Issue] = {}
    for index, spec in enumerate(ISSUES):
        issue = session.scalar(select(Issue).where(Issue.key == spec["key"]))
        if issue is not None:
            issues[spec["key"]] = issue
            continue
        created_at = now - timedelta(days=spec["created_offset"], hours=(index % 5) + 1)
        completed_at = (
            now - timedelta(days=spec["completed_offset"], hours=(index % 3) + 2)
            if spec.get("completed_offset")
            else None
        )
        sprint = sprints.get(spec["sprint"]) if spec["sprint"] else None
        issue = Issue(
            key=spec["key"],
            project_id=projects[spec["project"]].id,
            sprint_id=sprint.id if sprint else None,
            title=spec["title"],
            description=spec["description"],
            status=spec["status"],
            priority=spec["priority"],
            assignee_id=users[spec["assignee"]].id if spec["assignee"] else None,
            estimate=spec["estimate"],
            created_by_id=users[spec["creator"]].id,
            created_at=created_at,
            updated_at=completed_at or created_at,
            completed_at=completed_at,
        )
        issue.labels = [labels[name] for name in spec["labels"]]
        session.add(issue)
        session.flush()
        issues[spec["key"]] = issue

        session.add(
            ActivityEvent(
                issue_id=issue.id,
                actor_id=users[spec["creator"]].id,
                kind=ActivityKind.created,
                created_at=created_at,
            )
        )
        if completed_at is not None:
            session.add(
                ActivityEvent(
                    issue_id=issue.id,
                    actor_id=users[spec["assignee"] or spec["creator"]].id,
                    kind=ActivityKind.status_changed,
                    field="status",
                    from_value=IssueStatus.in_progress.value,
                    to_value=IssueStatus.done.value,
                    created_at=completed_at,
                )
            )
        for kind, field, from_value, to_value, days_ago in spec.get("history", []):
            session.add(
                ActivityEvent(
                    issue_id=issue.id,
                    actor_id=users[spec["assignee"] or spec["creator"]].id,
                    kind=ActivityKind(kind),
                    field=field,
                    from_value=from_value,
                    to_value=to_value,
                    created_at=now - timedelta(days=days_ago, hours=3),
                )
            )

    comment_count = 0
    for issue_key, author_name, body, days_ago in COMMENTS:
        issue = issues[issue_key]
        author = users[author_name]
        existing = session.scalar(
            select(Comment).where(
                Comment.issue_id == issue.id, Comment.author_id == author.id, Comment.body == body
            )
        )
        if existing is not None:
            continue
        created_at = now - timedelta(days=days_ago, hours=2)
        comment = Comment(issue_id=issue.id, author_id=author.id, body=body, created_at=created_at)
        session.add(comment)
        session.flush()
        session.add(
            ActivityEvent(
                issue_id=issue.id,
                actor_id=author.id,
                kind=ActivityKind.comment_added,
                created_at=created_at,
            )
        )
        comment_count += 1

    session.commit()
    return {
        "seeded": True,
        "users": len(users),
        "projects": len(projects),
        "sprints": len(sprints),
        "issues": len(issues),
        "comments": comment_count,
        "labels": len(labels),
    }


def run_seed(session: Session) -> dict:
    """Seed the workspace if it is empty; otherwise leave it untouched."""
    existing = session.scalar(select(User).limit(1))
    if existing is not None:
        return {"seeded": False, "reason": "workspace already seeded"}
    return _run_seed(session)


def describe_seed(summary: dict) -> str:
    if not summary.get("seeded"):
        return "[seed] workspace already seeded — nothing to do (idempotent)"
    return (
        "[seed] created {users} users, {projects} projects, {sprints} sprints, "
        "{issues} issues, {comments} comments and {labels} labels".format(**summary)
    )
