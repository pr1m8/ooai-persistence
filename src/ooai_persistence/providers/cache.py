"""Graph cache builders."""

from __future__ import annotations

from typing import Any

from ooai_persistence.settings import AppSettings


def build_graph_cache(settings: AppSettings) -> Any:
    """Build the configured graph cache."""
    if not settings.graph_cache.enabled or settings.graph_cache.backend == "none":
        return None
    if settings.graph_cache.backend == "memory":
        from langgraph.cache.memory import InMemoryCache

        return InMemoryCache()
    if settings.graph_cache.backend == "sqlite":
        from langgraph.cache.sqlite import SqliteCache

        path = settings.graph_cache.sqlite_path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return SqliteCache(path=str(path))
    raise ValueError(f"Unsupported graph cache backend: {settings.graph_cache.backend!r}.")
