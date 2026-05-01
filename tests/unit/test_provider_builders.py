"""Unit tests for persistence provider builders."""

from __future__ import annotations

import sys
import types
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, ClassVar

import pytest

from ooai_persistence.providers import cache, checkpointer, store
from ooai_persistence.settings import AppSettings


class _Factory:
    calls: ClassVar[list[tuple[str, Any]]] = []

    def __init__(self, value: str = "direct", **kwargs: Any) -> None:
        self.value = value
        self.kwargs = kwargs

    @classmethod
    def from_conn_string(cls, value: str, **kwargs: Any) -> _Factory:
        cls.calls.append((value, kwargs))
        return cls(value, **kwargs)


def _module(monkeypatch: pytest.MonkeyPatch, name: str, **symbols: Any) -> None:
    module = types.ModuleType(name)
    for symbol_name, symbol in symbols.items():
        setattr(module, symbol_name, symbol)
    monkeypatch.setitem(sys.modules, name, module)


def test_build_sqlite_checkpointer_creates_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SqliteSaver(_Factory):
        calls: ClassVar[list[tuple[str, Any]]] = []

    _module(monkeypatch, "langgraph.checkpoint.sqlite", SqliteSaver=SqliteSaver)
    settings = AppSettings.memory()
    settings.checkpointer.backend = "sqlite"
    settings.checkpointer.sqlite_path = tmp_path / "nested" / "state.sqlite3"

    with checkpointer.build_checkpointer(settings) as resource:
        assert isinstance(resource, SqliteSaver)
    assert settings.checkpointer.sqlite_path.parent.exists()


async def test_build_async_sqlite_checkpointer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class AsyncSqliteSaver(_Factory):
        calls: ClassVar[list[tuple[str, Any]]] = []

    _module(monkeypatch, "langgraph.checkpoint.sqlite.aio", AsyncSqliteSaver=AsyncSqliteSaver)
    settings = AppSettings.memory()
    settings.checkpointer.backend = "sqlite_async"
    settings.checkpointer.sqlite_path = tmp_path / "state.sqlite3"

    resource_context = await checkpointer.build_async_checkpointer(settings)

    async with resource_context as resource:
        assert isinstance(resource, AsyncSqliteSaver)


@pytest.mark.parametrize(
    ("backend", "module_name", "class_name"),
    [
        ("postgres", "langgraph.checkpoint.postgres", "PostgresSaver"),
        ("redis", "langgraph.checkpoint.redis", "RedisSaver"),
        ("mongodb", "langgraph.checkpoint.mongodb", "MongoDBSaver"),
    ],
)
def test_build_sync_network_checkpointers(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    module_name: str,
    class_name: str,
) -> None:
    fake_class = type(class_name, (_Factory,), {"calls": []})
    _module(monkeypatch, module_name, **{class_name: fake_class})
    settings = AppSettings.memory()
    settings.checkpointer.backend = backend  # type: ignore[assignment]

    resource = checkpointer.build_checkpointer(settings)

    if backend == "postgres":
        assert hasattr(resource, "__enter__")
        return
    assert isinstance(resource, fake_class)


@pytest.mark.parametrize(
    ("backend", "module_name", "class_name"),
    [
        ("postgres_async", "langgraph.checkpoint.postgres.aio", "AsyncPostgresSaver"),
        ("redis_async", "langgraph.checkpoint.redis.aio", "AsyncRedisSaver"),
        ("mongodb_async", "langgraph.checkpoint.mongodb.aio", "AsyncMongoDBSaver"),
    ],
)
async def test_build_async_network_checkpointers(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    module_name: str,
    class_name: str,
) -> None:
    fake_class = type(class_name, (_Factory,), {"calls": []})
    _module(monkeypatch, module_name, **{class_name: fake_class})
    settings = AppSettings.memory()
    settings.checkpointer.backend = backend  # type: ignore[assignment]

    resource = await checkpointer.build_async_checkpointer(settings)

    assert isinstance(resource, fake_class)


def test_build_sync_sqlite_store_creates_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SqliteStore(_Factory):
        calls: ClassVar[list[tuple[str, Any]]] = []

        @classmethod
        @contextmanager
        def from_conn_string(cls, value: str, **kwargs: Any) -> Iterator[SqliteStore]:
            yield cls(value, **kwargs)

    _module(monkeypatch, "langgraph.store.sqlite", SqliteStore=SqliteStore)
    settings = AppSettings.memory()
    settings.store.backend = "sqlite"
    settings.store.sqlite_path = tmp_path / "nested" / "store.sqlite3"

    with store.build_store(settings) as resource:
        assert isinstance(resource, SqliteStore)
    assert settings.store.sqlite_path.parent.exists()


async def test_build_async_sqlite_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class AsyncSqliteStore(_Factory):
        calls: ClassVar[list[tuple[str, Any]]] = []

        @classmethod
        @asynccontextmanager
        async def from_conn_string(
            cls,
            value: str,
            **kwargs: Any,
        ) -> AsyncIterator[AsyncSqliteStore]:
            yield cls(value, **kwargs)

    _module(monkeypatch, "langgraph.store.sqlite.aio", AsyncSqliteStore=AsyncSqliteStore)
    settings = AppSettings.memory()
    settings.store.backend = "sqlite_async"
    settings.store.sqlite_path = tmp_path / "store.sqlite3"

    resource_context = await store.build_async_store(settings)

    async with resource_context as resource:
        assert isinstance(resource, AsyncSqliteStore)


@pytest.mark.parametrize(
    ("backend", "module_name", "class_name"),
    [
        ("postgres", "langgraph.store.postgres", "PostgresStore"),
        ("redis", "langgraph.store.redis", "RedisStore"),
        ("mongodb", "langgraph.store.mongodb", "MongoDBStore"),
    ],
)
def test_build_sync_network_stores(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    module_name: str,
    class_name: str,
) -> None:
    fake_class = type(class_name, (_Factory,), {"calls": []})
    _module(monkeypatch, module_name, **{class_name: fake_class})
    settings = AppSettings.memory()
    settings.store.backend = backend  # type: ignore[assignment]

    resource = store.build_store(settings)

    assert isinstance(resource, fake_class)


@pytest.mark.parametrize(
    ("backend", "module_name", "class_name"),
    [
        ("postgres_async", "langgraph.store.postgres.aio", "AsyncPostgresStore"),
        ("redis_async", "langgraph.store.redis.aio", "AsyncRedisStore"),
        ("mongodb_async", "langgraph.store.mongodb.aio", "AsyncMongoDBStore"),
    ],
)
async def test_build_async_network_stores(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    module_name: str,
    class_name: str,
) -> None:
    fake_class = type(class_name, (_Factory,), {"calls": []})
    _module(monkeypatch, module_name, **{class_name: fake_class})
    settings = AppSettings.memory()
    settings.store.backend = backend  # type: ignore[assignment]

    resource = await store.build_async_store(settings)

    assert isinstance(resource, fake_class)


def test_build_sqlite_cache_creates_parent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class SqliteCache(_Factory):
        calls: ClassVar[list[tuple[str, Any]]] = []

    _module(monkeypatch, "langgraph.cache.sqlite", SqliteCache=SqliteCache)
    settings = AppSettings.memory()
    settings.graph_cache.backend = "sqlite"
    settings.graph_cache.sqlite_path = tmp_path / "nested" / "cache.sqlite3"

    resource = cache.build_graph_cache(settings)

    assert isinstance(resource, SqliteCache)
    assert settings.graph_cache.sqlite_path.parent.exists()


def test_explicit_sqlite_backend_requires_path() -> None:
    settings = AppSettings.memory()
    settings.checkpointer.backend = "sqlite"
    settings.checkpointer.sqlite_path = None

    with pytest.raises(ValueError, match="sqlite_path"):
        checkpointer.build_checkpointer(settings)
