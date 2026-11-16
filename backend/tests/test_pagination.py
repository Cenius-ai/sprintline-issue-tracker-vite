"""Every list endpoint honours limit/offset and reports X-Total-Count."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _assert_paginates(client: TestClient, headers: dict[str, str], path: str) -> None:
    """Assert the plain-array list contract: limit/offset plus X-Total-Count."""
    full = client.get(path, headers=headers)
    assert full.status_code == 200, full.text
    rows = full.json()
    assert rows, f"{path} should return seeded rows"
    total = int(full.headers["X-Total-Count"])
    assert total == len(rows), f"{path}: X-Total-Count must equal the full row count"

    first = client.get(f"{path}?limit=1&offset=0", headers=headers)
    assert first.status_code == 200
    assert int(first.headers["X-Total-Count"]) == total
    assert [row["id"] for row in first.json()] == [rows[0]["id"]]

    if total > 1:
        second = client.get(f"{path}?limit=1&offset=1", headers=headers)
        assert [row["id"] for row in second.json()] == [rows[1]["id"]]

    beyond = client.get(f"{path}?limit=5&offset={total + 5}", headers=headers)
    assert beyond.status_code == 200
    assert beyond.json() == []
    assert int(beyond.headers["X-Total-Count"]) == total

    assert client.get(f"{path}?limit=0", headers=headers).status_code == 422
    assert client.get(f"{path}?limit=500", headers=headers).status_code == 422
    assert client.get(f"{path}?offset=-1", headers=headers).status_code == 422


def test_reference_lists_paginate(client: TestClient, auth_headers):
    for path in ("/api/projects", "/api/users", "/api/labels"):
        _assert_paginates(client, auth_headers, path)


def test_sprint_list_paginates(client: TestClient, auth_headers):
    _assert_paginates(client, auth_headers, "/api/sprints")


def test_comment_list_paginates(client: TestClient, auth_headers):
    issue = next(
        item
        for item in client.get("/api/issues?q=SPL-2&limit=200", headers=auth_headers).json()["items"]
        if item["key"] == "SPL-2"
    )
    _assert_paginates(client, auth_headers, f"/api/issues/{issue['id']}/comments")


def test_filtered_sprint_list_paginates(client: TestClient, auth_headers):
    sprints = client.get("/api/sprints?status=active", headers=auth_headers)
    assert sprints.status_code == 200
    assert int(sprints.headers["X-Total-Count"]) == len(sprints.json()) == 1
    assert sprints.json()[0]["status"] == "active"
