"""Background model discovery for configured llama.cpp upstreams."""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.model import ModelCreate, ModelUpdate
from app.services.llamacpp import LlamaCppConnector
from app.services.model_registry import ModelRegistry
from app.services.http_client import get_http_client
from app.db.session import SessionLocal

logger = get_logger(__name__)
settings = get_settings()


class ModelDiscoveryService:
    """Probe configured upstreams and ensure healthy servers are registered."""

    async def discover_once(self) -> None:
        candidates = settings.model_discovery_candidates
        if not candidates:
            logger.info("Model discovery disabled or no upstream candidates configured.")
            return

        async with SessionLocal() as db:
            registry = ModelRegistry(db)
            connector = LlamaCppConnector(get_http_client())
            for candidate in candidates:
                ok, latency, detail = await connector.ping(candidate.endpoint_url)
                if not ok:
                    logger.info(
                        "Skipping unhealthy model upstream %s (%s): %s",
                        candidate.endpoint_url,
                        candidate.name,
                        detail,
                    )
                    continue

                model = await registry.get_by_name(candidate.name)
                if model is None:
                    logger.info(
                        "Registering discovered model %s at %s",
                        candidate.name,
                        candidate.endpoint_url,
                    )
                    await registry.create(
                        ModelCreate(
                            name=candidate.name,
                            provider="llamacpp",
                            endpoint_url=candidate.endpoint_url,
                            enabled=True,
                            capabilities=candidate.capabilities,
                        )
                    )
                elif model.endpoint_url != candidate.endpoint_url or not model.enabled:
                    logger.info(
                        "Updating discovered model %s to %s",
                        candidate.name,
                        candidate.endpoint_url,
                    )
                    await registry.update(
                        model,
                        ModelUpdate(
                            name=candidate.name,
                            provider="llamacpp",
                            endpoint_url=candidate.endpoint_url,
                            enabled=True,
                            capabilities=candidate.capabilities,
                        ),
                    )
            await db.commit()

    async def run(self, stop_event: asyncio.Event) -> None:
        interval = max(1, settings.model_discovery_interval)
        while not stop_event.is_set():
            try:
                await self.discover_once()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Model discovery failed: %s", exc)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue
