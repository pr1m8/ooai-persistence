"""End-to-end smoke tests for in-memory persistence flows."""

from ooai_persistence import AppSettings, run_async_smoke, run_sync_smoke


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
