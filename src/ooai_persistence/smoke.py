"""Reusable smoke checks for configured persistence bundles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from langgraph.checkpoint.base import empty_checkpoint

from ooai_persistence.context import open_persistence, open_sync_persistence
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings


@dataclass(slots=True)
class SmokeReport:
    """Result of exercising a persistence bundle."""

    mode: str
    checkpointer: str
    store: str
    graph_cache: str

    @property
    def ok(self) -> bool:
        """Return whether all configured resources passed."""
        return all(
            value in {"ok", "skipped"}
            for value in (self.checkpointer, self.store, self.graph_cache)
        )

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-friendly representation."""
        return asdict(self)


def _checkpoint_config(prefix: str) -> dict[str, dict[str, str]]:
    return {
        "configurable": {
            "thread_id": f"{prefix}-{uuid4()}",
            "checkpoint_ns": "",
        }
    }


def _store_namespace(prefix: str) -> tuple[str, str]:
    return ("ooai-persistence-smoke", f"{prefix}-{uuid4()}")


def _cache_key(prefix: str) -> tuple[tuple[str, str], str]:
    return (("ooai-persistence-smoke", prefix), str(uuid4()))


def _exercise_sync_checkpointer(checkpointer: Any) -> str:
    if checkpointer is None:
        return "skipped"
    config = _checkpoint_config("sync")
    saved_config = checkpointer.put(config, empty_checkpoint(), {}, {})
    checkpoint = checkpointer.get_tuple(saved_config)
    if checkpoint is None or checkpoint.config != saved_config:
        raise RuntimeError("Checkpointer smoke check failed to round-trip a checkpoint.")
    return "ok"


def _exercise_sync_store(store: Any) -> str:
    if store is None:
        return "skipped"
    namespace = _store_namespace("sync")
    store.put(namespace, "profile", {"name": "OOAI"})
    item = store.get(namespace, "profile")
    if item is None or item.value != {"name": "OOAI"}:
        raise RuntimeError("Store smoke check failed to round-trip an item.")
    return "ok"


def _exercise_sync_cache(graph_cache: Any) -> str:
    if graph_cache is None:
        return "skipped"
    key = _cache_key("sync")
    graph_cache.set({key: ("cached-value", None)})
    if graph_cache.get([key]) != {key: "cached-value"}:
        raise RuntimeError("Graph cache smoke check failed to round-trip a value.")
    return "ok"


async def _exercise_async_checkpointer(checkpointer: Any) -> str:
    if checkpointer is None:
        return "skipped"
    config = _checkpoint_config("async")
    saved_config = await checkpointer.aput(config, empty_checkpoint(), {}, {})
    checkpoint = await checkpointer.aget_tuple(saved_config)
    if checkpoint is None or checkpoint.config != saved_config:
        raise RuntimeError("Async checkpointer smoke check failed to round-trip a checkpoint.")
    return "ok"


async def _exercise_async_store(store: Any) -> str:
    if store is None:
        return "skipped"
    namespace = _store_namespace("async")
    await store.aput(namespace, "profile", {"name": "OOAI"})
    item = await store.aget(namespace, "profile")
    if item is None or item.value != {"name": "OOAI"}:
        raise RuntimeError("Async store smoke check failed to round-trip an item.")
    return "ok"


async def _exercise_async_cache(graph_cache: Any) -> str:
    if graph_cache is None:
        return "skipped"
    key = _cache_key("async")
    if hasattr(graph_cache, "aset") and hasattr(graph_cache, "aget"):
        await graph_cache.aset({key: ("cached-value", None)})
        result = await graph_cache.aget([key])
    else:
        graph_cache.set({key: ("cached-value", None)})
        result = graph_cache.get([key])
    if result != {key: "cached-value"}:
        raise RuntimeError("Async graph cache smoke check failed to round-trip a value.")
    return "ok"


def run_sync_smoke(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> SmokeReport:
    """Exercise sync checkpointer, store, and cache resources."""
    with open_sync_persistence(settings, registry=registry) as bundle:
        return SmokeReport(
            mode="sync",
            checkpointer=_exercise_sync_checkpointer(bundle.checkpointer),
            store=_exercise_sync_store(bundle.store),
            graph_cache=_exercise_sync_cache(bundle.graph_cache),
        )


async def run_async_smoke(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> SmokeReport:
    """Exercise async checkpointer, store, and cache resources."""
    async with open_persistence(settings, registry=registry) as bundle:
        return SmokeReport(
            mode="async",
            checkpointer=await _exercise_async_checkpointer(bundle.checkpointer),
            store=await _exercise_async_store(bundle.store),
            graph_cache=await _exercise_async_cache(bundle.graph_cache),
        )
