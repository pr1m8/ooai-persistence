"""Opt-in end-to-end tests for real Postgres persistence resources."""

from __future__ import annotations

import os

import pytest

from ooai_persistence import (
    AppSettings,
    open_postgres_persistence,
    open_postgres_store,
    open_sync_postgres_persistence,
    open_sync_postgres_store,
    run_async_smoke,
    run_sync_smoke,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("OOAI_PERSISTENCE_E2E_POSTGRES") != "1",
        reason="set OOAI_PERSISTENCE_E2E_POSTGRES=1 and provide Postgres settings",
    ),
]


def _postgres_settings() -> AppSettings:
    settings = AppSettings()
    settings.checkpointer.backend = "postgres"
    settings.store.backend = "postgres"
    settings.graph_cache.enabled = True
    settings.graph_cache.backend = "memory"
    return settings


def test_sync_postgres_bundle_round_trips_public_api() -> None:
    report = run_sync_smoke(_postgres_settings())

    assert report.ok is True
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


async def test_async_postgres_bundle_round_trips_public_api() -> None:
    report = await run_async_smoke(_postgres_settings())

    assert report.ok is True
    assert report.mode == "async"
    assert report.checkpointer == "ok"
    assert report.store == "ok"
    assert report.graph_cache == "ok"


def test_sync_postgres_wrappers_round_trip() -> None:
    with open_sync_postgres_persistence() as persistence:
        assert persistence.store is not None
        persistence.store.put(("users", "sync"), "profile", {"name": "OOAI"})
        item = persistence.store.get(("users", "sync"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    with open_sync_postgres_store() as store:
        store.put(("users", "sync-store"), "profile", {"name": "OOAI"})
        item = store.get(("users", "sync-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}


async def test_async_postgres_wrappers_round_trip() -> None:
    async with open_postgres_persistence() as persistence:
        assert persistence.store is not None
        await persistence.store.aput(("users", "async"), "profile", {"name": "OOAI"})
        item = await persistence.store.aget(("users", "async"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}

    async with open_postgres_store() as store:
        await store.aput(("users", "async-store"), "profile", {"name": "OOAI"})
        item = await store.aget(("users", "async-store"), "profile")
        assert item is not None
        assert item.value == {"name": "OOAI"}
