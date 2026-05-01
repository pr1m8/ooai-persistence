"""Top-level package for ``ooai_persistence``.

Purpose:
    Provide typed persistence helpers for LangGraph applications, including
    resource settings, serializer configuration, backend auto-resolution,
    and sync/async context helpers.
"""

from ooai_persistence.context import (
    async_persistence_context,
    open_persistence,
    open_sync_persistence,
    persistence_context,
)
from ooai_persistence.settings import AppSettings
from ooai_persistence.smoke import SmokeReport, run_async_smoke, run_sync_smoke

__all__ = [
    "AppSettings",
    "SmokeReport",
    "async_persistence_context",
    "open_persistence",
    "open_sync_persistence",
    "persistence_context",
    "run_async_smoke",
    "run_sync_smoke",
]
