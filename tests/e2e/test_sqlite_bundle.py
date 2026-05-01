"""End-to-end tests for real SQLite persistence resources."""

from __future__ import annotations

from pathlib import Path

from ooai_persistence import AppSettings, run_async_smoke, run_sync_smoke


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
