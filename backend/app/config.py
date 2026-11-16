"""Application settings.

Every value has a working default so the service boots on a bare clone with no
``.env`` file and no injected environment. Secrets are read with an in-code dev
fallback (never required from the environment); ``install.sh`` writes a random
JWT secret into ``backend/.env`` when one is not present, which then wins.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEV_JWT_SECRET = "cenius-dev-4b7c1f9a2d6e83509c7d3a51"


class Settings(BaseSettings):
    """Runtime configuration, tolerant of unknown environment keys."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sprintline Issue Tracker"
    # Relative SQLite file in the backend working directory; auto-created and
    # auto-seeded on the normal boot path.
    sprintline_database_url: str = "sqlite:///./app.db"

    # Auth: HS256 session tokens issued with PyJWT.
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "sprintline"
    jwt_expire_minutes: int = 720

    # Dev CORS: the Vite dev server proxies /api, so requests are same-origin,
    # but direct :8000 access is allowed too.
    cors_origins: str = "*"

    # Login throttling (single-process, windowed).
    login_attempts_per_email: int = 30
    login_attempts_per_ip: int = 120
    login_window_seconds: int = 60

    # Seed the demo workspace automatically when the database is empty.
    auto_seed: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def _secret_or_dev_fallback(cls, value: str) -> str:
        """An empty JWT_SECRET (e.g. a copied .env.example) falls back to dev."""
        return value.strip() or DEV_JWT_SECRET

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
