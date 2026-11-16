"""Auth, health and API envelope contracts."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from tests.conftest import DEMO_EMAIL, DEMO_PASSWORD


def test_health_reports_ok(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_root_serves_a_human_page(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "Sprintline" in body
    assert "cenius@cenius.ai" in body
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_login_with_demo_credential_returns_token_and_profile(client: TestClient):
    response = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["token"]
    assert payload["user"]["email"] == DEMO_EMAIL
    assert payload["user"]["name"] == "Cenius Demo"
    assert "password" not in payload["user"]
    assert "password_hash" not in payload["user"]


def test_login_is_case_insensitive_on_email(client: TestClient):
    response = client.post("/api/auth/login", json={"email": "Cenius@Cenius.AI", "password": DEMO_PASSWORD})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == DEMO_EMAIL


def test_wrong_password_is_one_generic_message(client: TestClient):
    response = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "***REDACTED-SECRET***"})
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "unauthorized"
    assert body["error"]["message"] == "Invalid email or password"
    assert "password" not in body["error"]["message"].lower() or "invalid email or password" in body[
        "error"
    ]["message"].lower()


def test_unknown_email_gives_the_same_message(client: TestClient):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_empty_password_is_rejected_with_validation_envelope(client: TestClient):
    response = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "password" in body["error"]["fields"]


def test_me_returns_the_current_user(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == DEMO_EMAIL


def test_me_requires_a_token(client: TestClient):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_protected_endpoint_rejects_expired_token(client: TestClient):
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {
            "sub": "1",
            "iat": int((now - timedelta(hours=3)).timestamp()),
            "exp": int((now - timedelta(hours=2)).timestamp()),
            "iss": "sprintline",
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    response = client.get("/api/issues", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_protected_endpoint_rejects_token_signed_with_another_secret(client: TestClient):
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {
            "sub": "1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iss": "sprintline",
        },
        "a-different-secret",
        algorithm="HS256",
    )
    response = client.get("/api/issues", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_unknown_route_uses_the_error_envelope(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/nope", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
