"""Application configuration.

Settings are loaded from environment variables (and an optional `.env` file).
A single cached `Settings` instance is exposed via `get_settings()`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class UpstreamCandidate(NamedTuple):
    """A model server the backend should try to auto-discover.

    ``name`` is the client-facing model id it gets registered under;
    ``endpoint_url`` is the in-network base URL; ``capabilities`` are the tags
    stored on the registry row.
    """

    name: str
    endpoint_url: str
    capabilities: list[str]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    app_name: str = "AirLLM Gateway"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # --- Server ---
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=4000)

    # --- Database ---
    # Standard SQLAlchemy URL. May be given with any postgres driver; it is
    # normalised to asyncpg for the app and to psycopg2 for Alembic.
    database_url: str = Field(
        default="postgresql+asyncpg://airllm:airllm@localhost:5432/airllm",
    )

    # --- Security ---
    # Used to protect the /admin endpoints (single shared admin token for Phase 1).
    admin_api_key: str = Field(default="changeme-admin-key")

    # --- CORS ---
    # Comma-separated list of allowed origins for the dashboard.
    cors_origins: str = Field(default="http://localhost:3000")

    # --- llama.cpp connector ---
    # Per-request timeout (seconds) when talking to upstream llama.cpp servers.
    upstream_timeout: float = Field(default=600.0)
    # Connection timeout used for health probes (seconds).
    health_timeout: float = Field(default=5.0)

    # --- Model discovery -----------------------------------------------------
    model_discovery_enabled: bool = Field(default=True)
    model_discovery_interval: int = Field(default=30)

    coder_upstream: str | None = Field(default=None)
    coder_model_name: str = Field(default="qwen2.5-coder")

    vision_upstream: str | None = Field(default=None)
    vision_model_name: str = Field(default="llava")

    deepseek_upstream: str | None = Field(default=None)
    deepseek_model_name: str = Field(default="deepseek-coder-v2-lite")

    @property
    def model_discovery_candidates(self) -> list[UpstreamCandidate]:
        candidates: list[UpstreamCandidate] = []
        if self.coder_upstream:
            candidates.append(
                UpstreamCandidate(
                    name=self.coder_model_name,
                    endpoint_url=self.coder_upstream,
                    capabilities=["chat"],
                )
            )
        if self.vision_upstream:
            candidates.append(
                UpstreamCandidate(
                    name=self.vision_model_name,
                    endpoint_url=self.vision_upstream,
                    capabilities=["vision", "chat"],
                )
            )
        if self.deepseek_upstream:
            candidates.append(
                UpstreamCandidate(
                    name=self.deepseek_model_name,
                    endpoint_url=self.deepseek_upstream,
                    capabilities=["chat"],
                )
            )
        return candidates

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Return the async (asyncpg) SQLAlchemy URL used by the app."""
        return self._normalize_db_url(self.database_url, "postgresql+asyncpg")

    @property
    def sync_database_url(self) -> str:
        """Return the sync (psycopg2) URL used by Alembic migrations."""
        return self._normalize_db_url(self.database_url, "postgresql+psycopg2")

    @staticmethod
    def _normalize_db_url(url: str, target_driver: str) -> str:
        """Swap whatever postgres driver is in `url` for `target_driver`."""
        for prefix in (
            "postgresql+asyncpg://",
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            "postgresql://",
            "postgres://",
        ):
            if url.startswith(prefix):
                return f"{target_driver}://" + url[len(prefix):]
        return url


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
