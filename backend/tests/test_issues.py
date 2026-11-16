"""Issues CRUD, filters, validation and activity side effects."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models import ActivityEvent
from app.seed import run_seed


def _projects(client: TestClient, headers: dict[str, str]) -> dict[str, int]:
    response = client.get("/api/projects", headers=headers)
    assert response.status_code == 200
    return {project["key"]: project["id"] for project in response.json()}


def _issue_by_key(client: TestClient, headers: dict[str, str], key: str) -> dict:
    for item in client.get(f"/api/issues?q={key}&limit=200", headers=headers).json()["items"]:
        if item["key"] == key:
            return item
    raise AssertionError(f"seeded issue {key} not found")


def test_seeded_workspace_has_two_projects_and_three_sprints(client: TestClient, auth_headers):
    projects = client.get("/api/projects", headers=auth_headers).json()
    sprints = client.get("/api/sprints", headers=auth_headers).json()
    users = client.get("/api/users", headers=auth_headers).json()
    labels = client.get("/api/labels", headers=auth_headers).json()
    issues = client.get("/api/issues?limit=200", headers=auth_headers).json()

    assert {project["key"] for project in projects} == {"SPL", "MOB"}
    assert len(sprints) == 3
    assert {sprint["status"] for sprint in sprints} == {"completed", "active", "planned"}
    assert len(users) == 4
    assert len(labels) >= 5
    assert issues["total"] == 24


def test_issue_list_expands_relations(client: TestClient, auth_headers):
    issues = client.get("/api/issues?limit=1", headers=auth_headers).json()["items"]
    issue = issues[0]
    assert issue["key"].startswith(("SPL-", "MOB-"))
    assert issue["project"]["key"] in {"SPL", "MOB"}
    assert isinstance(issue["labels"], list)
    assert "comment_count" in issue
    if issue["assignee"] is not None:
        assert {"id", "name", "avatar_color"} <= set(issue["assignee"])


def test_filter_by_status_and_priority(client: TestClient, auth_headers):
    response = client.get("/api/issues?status=in_progress&priority=high&limit=200", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items, "expected at least one in-progress high-priority issue in the seed"
    assert all(item["status"] == "in_progress" and item["priority"] == "high" for item in items)


def test_filter_by_search_matches_title_description_and_key(client: TestClient, auth_headers):
    by_title = client.get("/api/issues?q=burndown&limit=200", headers=auth_headers).json()["items"]
    assert by_title
    assert all(
        "burndown" in item["title"].lower() or "burndown" in item["description"].lower()
        for item in by_title
    )

    by_key = client.get("/api/issues?q=MOB-3", headers=auth_headers).json()["items"]
    assert [item["key"] for item in by_key] == ["MOB-3"]


def test_filter_unassigned_issues(client: TestClient, auth_headers):
    items = client.get("/api/issues?assignee_id=unassigned&limit=200", headers=auth_headers).json()["items"]
    assert items
    assert all(item["assignee"] is None for item in items)


def test_filter_by_label(client: TestClient, auth_headers):
    labels = {label["name"]: label["id"] for label in client.get("/api/labels", headers=auth_headers).json()}
    items = client.get(f"/api/issues?label_id={labels['bug']}&limit=200", headers=auth_headers).json()["items"]
    assert items
    assert all(any(label["name"] == "bug" for label in item["labels"]) for item in items)


def test_pagination_limits_and_offsets(client: TestClient, auth_headers):
    first = client.get("/api/issues?limit=5&offset=0", headers=auth_headers).json()
    second = client.get("/api/issues?limit=5&offset=5", headers=auth_headers).json()
    assert first["total"] == second["total"]
    assert len(first["items"]) == 5
    assert {item["id"] for item in first["items"]}.isdisjoint({item["id"] for item in second["items"]})


def test_create_issue_generates_a_key_and_records_activity(client: TestClient, auth_headers):
    projects = _projects(client, auth_headers)
    sprint = client.get("/api/sprints?status=active", headers=auth_headers).json()[0]
    labels = client.get("/api/labels", headers=auth_headers).json()[:2]
    assignee = client.get("/api/users", headers=auth_headers).json()[0]

    response = client.post(
        "/api/issues",
        headers=auth_headers,
        json={
            "title": "Roadmap view drops issues without a sprint",
            "description": "Later lane renders empty when every issue in the project has a sprint.",
            "status": "todo",
            "priority": "high",
            "project_id": projects["SPL"],
            "sprint_id": sprint["id"],
            "assignee_id": assignee["id"],
            "estimate": 3,
            "label_ids": [label["id"] for label in labels],
        },
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["key"].startswith("SPL-")
    assert created["key"].split("-")[1].isdigit()
    assert len(created["labels"]) == 2
    assert created["sprint"]["name"] == sprint["name"]

    listed = client.get("/api/issues?limit=200", headers=auth_headers).json()
    assert listed["items"][0]["id"] == created["id"]
    assert listed["total"] == 25

    activity = client.get(f"/api/issues/{created['id']}/activity", headers=auth_headers).json()["items"]
    assert any(event["kind"] == "created" for event in activity)

    # clean up so the rest of the suite sees the seeded total again
    assert client.delete(f"/api/issues/{created['id']}", headers=auth_headers).status_code == 204


def test_create_issue_rejects_blank_title(client: TestClient, auth_headers):
    projects = _projects(client, auth_headers)
    before = client.get("/api/issues?limit=1", headers=auth_headers).json()["total"]
    response = client.post(
        "/api/issues",
        headers=auth_headers,
        json={"title": "   ", "project_id": projects["SPL"]},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "title" in body["error"]["fields"]
    after = client.get("/api/issues?limit=1", headers=auth_headers).json()["total"]
    assert after == before


def test_create_issue_rejects_unknown_project(client: TestClient, auth_headers):
    response = client.post("/api/issues", headers=auth_headers, json={"title": "Ghost", "project_id": 9999})
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Unknown project"


def test_patch_status_to_done_sets_completed_at_and_records_event(client: TestClient, auth_headers):
    target = client.get("/api/issues?status=todo&limit=50", headers=auth_headers).json()["items"][0]
    assert target["completed_at"] is None

    response = client.patch(f"/api/issues/{target['id']}", headers=auth_headers, json={"status": "done"})
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "done"
    assert updated["completed_at"] is not None

    activity = client.get(f"/api/issues/{target['id']}/activity", headers=auth_headers).json()["items"]
    assert activity[0]["kind"] == "status_changed"
    assert activity[0]["from_value"] == "todo"
    assert activity[0]["to_value"] == "done"

    # move it back so the seed's distribution is unchanged for other tests
    restored = client.patch(f"/api/issues/{target['id']}", headers=auth_headers, json={"status": "todo"})
    assert restored.status_code == 200
    assert restored.json()["completed_at"] is None


def test_patch_priority_records_event(client: TestClient, auth_headers):
    target = client.get("/api/issues?priority=low&limit=5", headers=auth_headers).json()["items"][0]
    response = client.patch(f"/api/issues/{target['id']}", headers=auth_headers, json={"priority": "urgent"})
    assert response.status_code == 200
    assert response.json()["priority"] == "urgent"

    activity = client.get(f"/api/issues/{target['id']}/activity", headers=auth_headers).json()["items"]
    assert activity[0]["kind"] == "priority_changed"
    assert activity[0]["to_value"] == "urgent"

    client.patch(f"/api/issues/{target['id']}", headers=auth_headers, json={"priority": "low"})


def test_patch_assignee_and_sprint_records_events(client: TestClient, auth_headers):
    users = client.get("/api/users", headers=auth_headers).json()
    target = _issue_by_key(client, auth_headers, "SPL-3")
    original_assignee = target["assignee"]["id"]
    original_sprint = target["sprint"]["id"]
    new_assignee = next(user["id"] for user in users if user["id"] != original_assignee)

    response = client.patch(
        f"/api/issues/{target['id']}",
        headers=auth_headers,
        json={"assignee_id": new_assignee, "sprint_id": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assignee"]["id"] == new_assignee
    assert body["sprint"] is None

    newest = client.get(f"/api/issues/{target['id']}/activity", headers=auth_headers).json()["items"]
    kinds = {event["kind"] for event in newest[:4]}
    assert {"assignee_changed", "sprint_changed"} <= kinds

    restored = client.patch(
        f"/api/issues/{target['id']}",
        headers=auth_headers,
        json={"assignee_id": original_assignee, "sprint_id": original_sprint},
    )
    assert restored.status_code == 200
    assert restored.json()["sprint"]["id"] == original_sprint


def test_delete_issue_removes_it_and_its_children(client: TestClient, auth_headers):
    projects = _projects(client, auth_headers)
    created = client.post(
        "/api/issues",
        headers=auth_headers,
        json={"title": "Throwaway issue for the delete contract", "project_id": projects["MOB"]},
    ).json()
    client.post(f"/api/issues/{created['id']}/comments", headers=auth_headers, json={"body": "delete me"})

    assert client.delete(f"/api/issues/{created['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/issues/{created['id']}", headers=auth_headers).status_code == 404

    with SessionLocal() as session:
        remaining = session.query(ActivityEvent).filter(ActivityEvent.issue_id == created["id"]).count()
    assert remaining == 0


def test_missing_issue_returns_404_envelope(client: TestClient, auth_headers):
    response = client.get("/api/issues/999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_seed_is_idempotent():
    with SessionLocal() as session:
        summary = run_seed(session)
    assert summary["seeded"] is False
