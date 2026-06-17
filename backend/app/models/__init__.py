"""ORM models package.

Importing this package ensures every model module is loaded so that
``Base.metadata`` is fully populated (used by Alembic autogenerate and by the
test bootstrap that creates tables directly).
"""

from __future__ import annotations

from app.db.base import Base
from app.models.api_key import ApiKey
from app.models.model import Model
from app.models.request_log import RequestLog

__all__ = ["Base", "ApiKey", "Model", "RequestLog"]
