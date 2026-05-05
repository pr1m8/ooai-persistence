"""End-to-end smoke tests for in-memory persistence flows."""

from ooai_persistence import (
    AppSettings,
    open_memory_persistence,
    open_memory_store,
    open_sync_memory_persistence,
    open_sync_memory_store,
    run_async_smoke,
    run_sync_smoke,
)


def test_memory_persistence_bundle_end_to_end() -> None:
    report = run_sync_smoke(AppSettings.memory())

    assert report.ok is True
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


async def test_async_memory_persistence_bundle_end_to_end() -> None:
    report = await run_async_smoke(AppSettings.memory())

    assert report.ok is True
    assert report.mode == "async"
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


def test_sync_memory_wrappers_round_trip() -> None:
    with open_sync_memory_persistence() as persistence:
        assert persistence.store is not None
        persistence.store.put(("users", "sync"), "profile", {"name": "OOAI"})
        item = persistence.store.get(("users", "sync"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    with open_sync_memory_store() as store:
        store.put(("users", "sync-store"), "profile", {"name": "OOAI"})
        item = store.get(("users", "sync-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}


async def test_async_memory_wrappers_round_trip() -> None:
    async with open_memory_persistence() as persistence:
        assert persistence.store is not None
        await persistence.store.aput(("users", "async"), "profile", {"name": "OOAI"})
        item = await persistence.store.aget(("users", "async"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    async with open_memory_store() as store:
        await store.aput(("users", "async-store"), "profile", {"name": "OOAI"})
        item = await store.aget(("users", "async-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}
