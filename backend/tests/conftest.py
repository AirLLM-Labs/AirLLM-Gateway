"""Pytest fixtures.

Tests run against an in-memory async SQLite database (no Postgres required).
A shared StaticPool connection keeps the same in-memory schema across sessions.
The ``get_db`` dependency and the logging middleware's sessionmaker are both
pointed at this test database.
"""

from __future__ import annotations

import os

# Ensure settings import doesn't pick up a developer .env with a real DB.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://airllm:airllm@localhost:5432/airllm")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-token")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

ADMIN_TOKEN = get_settings().admin_api_key
ADMIN_HEADERS = {"X-Admin-Token": ADMIN_TOKEN}


@pytest_asyncio.fixture
async def db_sessionmaker():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    yield maker

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_sessionmaker, monkeypatch):
    async def _get_db_override():
        async with db_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Point the request-logging middleware *and* the chat streaming logger at
    # the test DB too (both open their own session outside the request scope).
    monkeypatch.setattr("app.middleware.request_logging.SessionLocal", db_sessionmaker)
    monkeypatch.setattr("app.api.v1.chat.SessionLocal", db_sessionmaker)
    app.dependency_overrides[get_db] = _get_db_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
