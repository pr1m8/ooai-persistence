"""Store resource builders."""
# pyright: reportMissingImports=false

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from ooai_persistence.registry import resolve_backend
from ooai_persistence.settings import AppSettings


def _ensure_parent(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _sqlite_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("SQLite store backend requires store.sqlite_path.")
    return _ensure_parent(path)


def _postgres_pool_config(settings: AppSettings) -> Any | None:
    infra = settings.infra
    if infra.postgres_pool_min_size is None and infra.postgres_pool_max_size is None:
        return None
    return cast(
        Any,
        {
        "min_size": infra.postgres_pool_min_size,
        "max_size": infra.postgres_pool_max_size,
        "kwargs": {},
        },
    )


def build_store(settings: AppSettings) -> Any:
    """Build the configured synchronous long-term store."""
    backend = resolve_backend(settings.store, settings, prefer_async=False)
    if backend == "none":
        return None
    if backend == "memory":
        from langgraph.store.memory import InMemoryStore

        return InMemoryStore()
    if backend == "sqlite":
        from langgraph.store.sqlite import SqliteStore

        path = _sqlite_path(settings.store.sqlite_path)
        return SqliteStore.from_conn_string(str(path))
    if backend == "postgres":
        from langgraph.store.postgres import PostgresStore

        uri = settings.store.postgres_uri or settings.infra.postgres_uri
        return PostgresStore.from_conn_string(uri, pool_config=_postgres_pool_config(settings))
    if backend == "redis":
        from langgraph.store.redis import RedisStore

        url = settings.store.redis_url or settings.infra.redis_url
        return RedisStore.from_conn_string(url)
    if backend == "mongodb":
        from langgraph.store.mongodb import MongoDBStore

        uri = settings.store.mongodb_uri or settings.infra.mongodb_uri
        return MongoDBStore.from_conn_string(uri)
    raise ValueError(f"Unsupported synchronous store backend: {backend!r}.")


async def build_async_store(settings: AppSettings) -> Any:
    """Build the configured asynchronous long-term store."""
    backend = resolve_backend(settings.store, settings, prefer_async=True)
    if backend == "none":
        return None
    if backend == "memory":
        from langgraph.store.memory import InMemoryStore

        return InMemoryStore()
    if backend == "sqlite_async":
        from langgraph.store.sqlite.aio import AsyncSqliteStore

        path = _sqlite_path(settings.store.sqlite_path)
        return AsyncSqliteStore.from_conn_string(str(path))
    if backend == "postgres_async":
        from langgraph.store.postgres.aio import AsyncPostgresStore

        uri = settings.store.postgres_uri or settings.infra.postgres_uri
        return AsyncPostgresStore.from_conn_string(
            uri,
            pool_config=_postgres_pool_config(settings),
        )
    if backend == "redis_async":
        from langgraph.store.redis.aio import AsyncRedisStore

        url = settings.store.redis_url or settings.infra.redis_url
        return AsyncRedisStore.from_conn_string(url)
    if backend == "mongodb_async":
        from langgraph.store.mongodb.aio import AsyncMongoDBStore

        uri = settings.store.mongodb_uri or settings.infra.mongodb_uri
        return AsyncMongoDBStore.from_conn_string(uri)
    raise ValueError(f"Unsupported asynchronous store backend: {backend!r}.")
