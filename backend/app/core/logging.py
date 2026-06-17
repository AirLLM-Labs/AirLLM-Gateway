"""Centralized logging configuration."""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once, using the level from settings."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on reload.
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (ensuring logging is configured)."""
    configure_logging()
    return logging.getLogger(name)
