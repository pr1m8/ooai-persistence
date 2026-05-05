"""Integration tests for async persistence context."""

import pytest

from ooai_persistence.context import (
    async_persistence_context,
    open_memory_persistence,
    open_sync_memory_persistence,
)
from ooai_persistence.settings import AppSettings


@pytest.mark.integration
async def test_async_persistence_context_memory() -> None:
    settings = AppSettings.memory()
    async with async_persistence_context(settings) as bundle:
        assert bundle.checkpointer is not None
        assert bundle.store is not None
        assert bundle.graph_cache is not None


@pytest.mark.integration
async def test_open_memory_persistence_async_helper() -> None:
    async with open_memory_persistence() as bundle:
        assert bundle.checkpointer is not None
        assert bundle.store is not None


@pytest.mark.integration
def test_open_memory_persistence_sync_helper() -> None:
    with open_sync_memory_persistence() as bundle:
        assert bundle.checkpointer is not None
        assert bundle.store is not None
