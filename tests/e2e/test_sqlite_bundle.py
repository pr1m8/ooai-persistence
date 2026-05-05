"""End-to-end tests for real SQLite persistence resources."""

from __future__ import annotations

from pathlib import Path

from ooai_persistence import (
    AppSettings,
    open_sqlite_persistence,
    open_sqlite_store,
    open_sync_sqlite_persistence,
    open_sync_sqlite_store,
    run_async_smoke,
    run_sync_smoke,
)


def _sqlite_settings(tmp_path: Path) -> AppSettings:
    settings = AppSettings.local_sqlite(tmp_path / "state.sqlite3")
    settings.graph_cache.enabled = True
    settings.graph_cache.backend = "sqlite"
    settings.graph_cache.sqlite_path = tmp_path / "graph-cache.sqlite3"
    return settings


def test_sync_sqlite_bundle_round_trips_public_api(tmp_path: Path) -> None:
    report = run_sync_smoke(_sqlite_settings(tmp_path))

    assert report.ok is True
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


async def test_async_sqlite_bundle_round_trips_public_api(tmp_path: Path) -> None:
    report = await run_async_smoke(_sqlite_settings(tmp_path))

    assert report.ok is True
    assert report.mode == "async"
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


def test_sync_sqlite_wrappers_round_trip(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "wrapper.sqlite3"

    with open_sync_sqlite_persistence(sqlite_path) as persistence:
        assert persistence.store is not None
        persistence.store.put(("users", "sync"), "profile", {"name": "OOAI"})
        item = persistence.store.get(("users", "sync"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    with open_sync_sqlite_store(sqlite_path) as store:
        store.put(("users", "sync-store"), "profile", {"name": "OOAI"})
        item = store.get(("users", "sync-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}


async def test_async_sqlite_wrappers_round_trip(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "wrapper-async.sqlite3"

    async with open_sqlite_persistence(sqlite_path) as persistence:
        assert persistence.store is not None
        await persistence.store.aput(("users", "async"), "profile", {"name": "OOAI"})
        item = await persistence.store.aget(("users", "async"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    async with open_sqlite_store(sqlite_path) as store:
        await store.aput(("users", "async-store"), "profile", {"name": "OOAI"})
        item = await store.aget(("users", "async-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}
