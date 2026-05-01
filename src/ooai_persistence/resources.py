"""Convenience resource-loading helpers for ``ooai_persistence``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ooai_persistence.providers.cache import build_graph_cache
from ooai_persistence.providers.checkpointer import build_async_checkpointer, build_checkpointer
from ooai_persistence.providers.store import build_async_store, build_store
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings


@dataclass(slots=True)
class PersistenceBundle:
    """Collection of persistence-related resources."""

    checkpointer: Any | None
    store: Any | None
    graph_cache: Any | None


@dataclass(slots=True)
class PersistenceBuildReport:
    """Information about resolved persistence choices."""

    checkpointer_backend: str
    store_backend: str
    graph_cache_backend: str


def build_persistence_bundle(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> PersistenceBundle:
    """Build a synchronous persistence bundle."""
    return PersistenceBundle(
        checkpointer=build_checkpointer(settings, registry=registry),
        store=build_store(settings),
        graph_cache=build_graph_cache(settings),
    )


async def build_async_persistence_bundle(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> PersistenceBundle:
    """Build an asynchronous persistence bundle."""
    return PersistenceBundle(
        checkpointer=await build_async_checkpointer(settings, registry=registry),
        store=await build_async_store(settings),
        graph_cache=build_graph_cache(settings),
    )
