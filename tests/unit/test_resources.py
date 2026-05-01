"""Unit tests for local resource builders."""

from ooai_persistence.providers.cache import build_graph_cache
from ooai_persistence.settings import AppSettings


def test_build_memory_graph_cache() -> None:
    settings = AppSettings.model_validate({"graph_cache": {"enabled": True, "backend": "memory"}})
    cache = build_graph_cache(settings)
    assert cache is not None
