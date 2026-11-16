"""pytest configuration: isolated SQLite database, seeded once per session."""

from __future__ import annotations

import os
import pathlib
import tempfile

# Configure the database BEFORE the application modules import app.config.
_TEST_DIR = pathlib.Path(tempfile.mkdtemp(prefix="sprintline-tests-"))
os.environ["SPRINTLINE_DATABASE_URL"] = f"sqlite:///{_TEST_DIR / 'test.db'}"
os.environ["JWT_SECRET"] = "test-only-secret-9d1c4f7a2b6e8305"
os.environ["AUTO_SEED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, ensure_schema  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import run_seed  # noqa: E402

DEMO_EMAIL = "cenius@cenius.ai"
DEMO_PASSWORD = "cenius"


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    """Create the schema and seed the demo workspace exactly once."""
    ensure_schema()
    with SessionLocal() as session:
        run_seed(session)
    yield


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}
