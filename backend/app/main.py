"""AirLLM Gateway application factory and ASGI entrypoint.

Run with: ``uvicorn app.main:app --host 0.0.0.0 --port 4000``.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health as health_api
from app.api.admin import router as admin_router
from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.http_client import shutdown_http_client, startup_http_client
from app.services.model_discovery import ModelDiscoveryService

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s v%s", settings.app_name, __version__)
    await startup_http_client()

    discovery_task: asyncio.Task | None = None
    discovery_stop: asyncio.Event | None = None
    if settings.model_discovery_enabled:
        discovery_service = ModelDiscoveryService()
        await discovery_service.discover_once()
        discovery_stop = asyncio.Event()
        discovery_task = asyncio.create_task(discovery_service.run(discovery_stop))
        app.state.model_discovery_task = discovery_task
        app.state.model_discovery_stop = discovery_stop

    try:
        yield
    finally:
        if discovery_task and discovery_stop:
            discovery_stop.set()
            discovery_task.cancel()
            with suppress(asyncio.CancelledError):
                await discovery_task
        await shutdown_http_client()
        await dispose_engine()
        logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Self-hosted, OpenAI-compatible gateway for local llama.cpp models.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Request logging wraps inference traffic.
    app.add_middleware(RequestLoggingMiddleware)

    # Routers.
    app.include_router(health_api.router)
    app.include_router(v1_router)
    app.include_router(admin_router)

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
