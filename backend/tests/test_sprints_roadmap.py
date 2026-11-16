"""Sprint totals, derived burndown series and roadmap lane derivation."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _sprints(client: TestClient, headers: dict[str, str]) -> dict[str, dict]:
    response = client.get("/api/sprints", headers=headers)
    assert response.status_code == 200
    sprints = response.json()
    return {sprint["status"]: sprint for sprint in sprints}


def test_sprint_list_has_counts_and_date_ranges(client: TestClient, auth_headers):
    sprints = _sprints(client, auth_headers)
    assert set(sprints) == {"completed", "active", "planned"}
    active = sprints["active"]
    assert active["point_count"] > 0
    assert active["issue_count"] > 0
    assert active["done_count"] >= 1
    assert active["start_date"] < active["end_date"]
    assert active["project_key"] == "SPL"
    assert active["goal"]


def test_sprint_detail_matches_list(client: TestClient, auth_headers):
    active = _sprints(client, auth_headers)["active"]
    response = client.get(f"/api/sprints/{active['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == active["name"]


def test_missing_sprint_is_404(client: TestClient, auth_headers):
    assert client.get("/api/sprints/999999", headers=auth_headers).status_code == 404
    assert client.get("/api/sprints/999999/burndown", headers=auth_headers).status_code == 404


def test_burndown_series_is_derived_from_dates_and_completions(client: TestClient, auth_headers):
    active = _sprints(client, auth_headers)["active"]
    response = client.get(f"/api/sprints/{active['id']}/burndown", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["sprint_id"] == active["id"]
    assert body["total_points"] == active["point_count"]
    assert body["days"] == len(body["points"]) >= 10
    ideal = [point["ideal"] for point in body["points"]]
    actual = [point["actual"] for point in body["points"]]

    assert ideal[0] == body["total_points"]
    assert ideal[-1] == 0
    assert all(first >= second for first, second in zip(ideal, ideal[1:]))
    assert all(first >= second for first, second in zip(actual, actual[1:]))
    assert actual[0] == body["total_points"]
    assert body["completed_points"] > 0
    assert actual[-1] == body["total_points"] - body["completed_points"]


def test_completed_sprint_burndown_ends_above_zero(client: TestClient, auth_headers):
    completed = _sprints(client, auth_headers)["completed"]
    body = client.get(f"/api/sprints/{completed['id']}/burndown", headers=auth_headers).json()
    assert body["completed_points"] > 0
    assert body["points"][-1]["actual"] >= 0


def test_roadmap_groups_projects_into_four_lanes(client: TestClient, auth_headers):
    response = client.get("/api/roadmap", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["lanes"] == ["now", "next", "later", "done"]
    assert len(body["projects"]) == 2

    by_key = {row["project"]["key"]: row for row in body["projects"]}
    spl = by_key["SPL"]
    assert spl["lanes"]["now"] and spl["lanes"]["next"] and spl["lanes"]["later"] and spl["lanes"]["done"]
    for lane, cards in spl["lanes"].items():
        assert spl["counts"][lane] == len(cards)
        for card in cards:
            assert {"key", "title", "status", "priority"} <= set(card)


def test_roadmap_puts_active_sprint_issues_in_now(client: TestClient, auth_headers):
    active = _sprints(client, auth_headers)["active"]
    in_sprint = client.get(f"/api/issues?sprint_id={active['id']}&limit=200", headers=auth_headers).json()["items"]
    open_in_sprint = {issue["key"] for issue in in_sprint if issue["status"] != "done"}
    roadmap = client.get("/api/roadmap", headers=auth_headers).json()
    spl = next(row for row in roadmap["projects"] if row["project"]["key"] == "SPL")
    now_keys = {card["key"] for card in spl["lanes"]["now"]}
    assert open_in_sprint <= now_keys
    assert all(card["status"] != "done" for card in spl["lanes"]["now"])
    assert all(card["status"] == "done" for card in spl["lanes"]["done"])


def test_roadmap_can_be_filtered_to_one_project(client: TestClient, auth_headers):
    projects = client.get("/api/projects", headers=auth_headers).json()
    mob = next(project for project in projects if project["key"] == "MOB")
    response = client.get(f"/api/roadmap?project_id={mob['id']}", headers=auth_headers)
    assert response.status_code == 200
    rows = response.json()["projects"]
    assert len(rows) == 1
    assert rows[0]["project"]["key"] == "MOB"
    assert rows[0]["lanes"]["later"], "mobile backlog should populate the Later lane"
