"""Process runtime helpers.

Tracks when the process started so the dashboard can show uptime. The start
time is captured at import (module load happens during app startup).
"""

from __future__ import annotations

import time

_STARTED_AT_MONOTONIC = time.monotonic()


def uptime_seconds() -> int:
    """Whole seconds since the process started."""
    return int(time.monotonic() - _STARTED_AT_MONOTONIC)
