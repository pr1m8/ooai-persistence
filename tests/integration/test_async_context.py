"""Integration tests for async persistence context."""

import pytest

from ooai_persistence.context import async_persistence_context
from ooai_persistence.settings import AppSettings


@pytest.mark.integration
async def test_async_persistence_context_memory() -> None:
    settings = AppSettings.memory()
    async with async_persistence_context(settings) as bundle:
        assert bundle.checkpointer is not None
        assert bundle.store is not None
        assert bundle.graph_cache is not None
