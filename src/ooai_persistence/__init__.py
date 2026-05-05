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
from ooai_persistence.graphs import (
    PersistentGraph,
    bind_graph_with_persistence,
    compile_graph_with_persistence,
    open_graph,
    open_sync_graph,
)
from ooai_persistence.settings import (
    AppSettings,
    memory_settings,
    postgres_settings,
    sqlite_settings,
)
from ooai_persistence.smoke import SmokeReport, run_async_smoke, run_sync_smoke

__all__ = [
    "AppSettings",
    "PersistentGraph",
    "SmokeReport",
    "async_persistence_context",
    "bind_graph_with_persistence",
    "compile_graph_with_persistence",
    "memory_settings",
    "open_graph",
    "open_persistence",
    "open_sync_graph",
    "open_sync_persistence",
    "persistence_context",
    "postgres_settings",
    "run_async_smoke",
    "run_sync_smoke",
    "sqlite_settings",
]
