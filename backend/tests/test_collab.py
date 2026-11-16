"""Comments and activity history contracts."""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient


def _issue_by_key(client: TestClient, headers: dict[str, str], key: str) -> dict:
    items = client.get(f"/api/issues?q={key}", headers=headers).json()["items"]
    for item in items:
        if item["key"] == key:
            return item
    raise AssertionError(f"seeded issue {key} not found")


def _parse(timestamp: str) -> datetime:
    assert timestamp.endswith("Z"), f"expected UTC ISO timestamp, got {timestamp}"
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_comments_are_oldest_first_with_authors(client: TestClient, auth_headers):
    issue = _issue_by_key(client, auth_headers, "SPL-2")
    response = client.get(f"/api/issues/{issue['id']}/comments", headers=auth_headers)
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) >= 2
    assert [comment["created_at"] for comment in comments] == sorted(
        comment["created_at"] for comment in comments
    )
    assert all(comment["author"]["name"] for comment in comments)
    assert all(comment["body"] for comment in comments)
    assert issue["comment_count"] == len(comments)


def test_post_comment_appends_and_records_activity(client: TestClient, auth_headers):
    issue = _issue_by_key(client, auth_headers, "SPL-13")
    before = client.get(f"/api/issues/{issue['id']}/comments", headers=auth_headers).json()

    response = client.post(
        f"/api/issues/{issue['id']}/comments",
        headers=auth_headers,
        json={"body": "Looks good, shipping today"},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["body"] == "Looks good, shipping today"
    assert created["author"]["email"] == "cenius@cenius.ai"

    after = client.get(f"/api/issues/{issue['id']}/comments", headers=auth_headers).json()
    assert len(after) == len(before) + 1
    assert after[-1]["id"] == created["id"]

    activity = client.get(f"/api/issues/{issue['id']}/activity", headers=auth_headers).json()["items"]
    assert activity[0]["kind"] == "comment_added"
    assert activity[0]["actor"]["email"] == "cenius@cenius.ai"


def test_empty_comment_is_rejected(client: TestClient, auth_headers):
    issue = _issue_by_key(client, auth_headers, "SPL-9")
    before = len(client.get(f"/api/issues/{issue['id']}/comments", headers=auth_headers).json())
    response = client.post(f"/api/issues/{issue['id']}/comments", headers=auth_headers, json={"body": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    after = len(client.get(f"/api/issues/{issue['id']}/comments", headers=auth_headers).json())
    assert after == before


def test_comment_on_missing_issue_is_404(client: TestClient, auth_headers):
    response = client.post("/api/issues/999999/comments", headers=auth_headers, json={"body": "hello"})
    assert response.status_code == 404


def test_activity_is_newest_first_with_readable_changes(client: TestClient, auth_headers):
    issue = _issue_by_key(client, auth_headers, "SPL-2")
    response = client.get(f"/api/issues/{issue['id']}/activity", headers=auth_headers)
    assert response.status_code == 200
    events = response.json()["items"]
    assert len(events) >= 3
    timestamps = [_parse(event["created_at"]) for event in events]
    assert timestamps == sorted(timestamps, reverse=True)
    status_changes = [event for event in events if event["kind"] == "status_changed"]
    assert status_changes
    assert status_changes[0]["field"] == "status"
    assert status_changes[0]["to_value"] == "done"
    assert status_changes[0]["actor"]["name"]
    assert events[0]["issue_key"] == "SPL-2"


def test_workspace_activity_feed(client: TestClient, auth_headers):
    response = client.get("/api/activity?limit=8", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 8
    assert len(body["items"]) == 8
    assert all(event["issue_key"] for event in body["items"])
    assert all(event["actor"]["name"] for event in body["items"])
