"""Checkpointer resource builders."""
# pyright: reportMissingImports=false

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing, contextmanager
from pathlib import Path
from typing import Any

from ooai_persistence.registry import resolve_backend
from ooai_persistence.serde.builders import build_checkpointer_serde
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings


def _ensure_parent(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _sqlite_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("SQLite checkpointer backend requires checkpointer.sqlite_path.")
    return _ensure_parent(path)


@contextmanager
def _open_sqlite_saver(path: Path, serde: Any) -> Iterator[Any]:
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    with closing(sqlite3.connect(str(path), check_same_thread=False)) as conn:
        yield SqliteSaver(conn, serde=serde)


@asynccontextmanager
async def _open_async_sqlite_saver(path: Path, serde: Any) -> AsyncIterator[Any]:
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    async with aiosqlite.connect(str(path)) as conn:
        yield AsyncSqliteSaver(conn, serde=serde)


@contextmanager
def _open_postgres_saver(uri: str, serde: Any) -> Iterator[Any]:
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg import Connection
    from psycopg.rows import dict_row

    with Connection.connect(  # type: ignore[reportArgumentType]
        uri,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,  # type: ignore[reportArgumentType]
    ) as conn:
        postgres_conn: Any = conn
        yield PostgresSaver(postgres_conn, serde=serde)


def build_checkpointer(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Any:
    """Build the configured synchronous checkpointer."""
    backend = resolve_backend(settings.checkpointer, settings, prefer_async=False)
    serde = build_checkpointer_serde(settings, registry=registry)

    if backend == "none":
        return None
    if backend == "memory":
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver(serde=serde)
    if backend == "sqlite":
        path = _sqlite_path(settings.checkpointer.sqlite_path)
        return _open_sqlite_saver(path, serde)
    if backend == "postgres":
        uri = settings.checkpointer.postgres_uri or settings.infra.postgres_uri
        return _open_postgres_saver(uri, serde)
    if backend == "redis":
        from langgraph.checkpoint.redis import RedisSaver

        url = settings.checkpointer.redis_url or settings.infra.redis_url
        return RedisSaver.from_conn_string(url)
    if backend == "mongodb":
        from langgraph.checkpoint.mongodb import MongoDBSaver

        uri = settings.checkpointer.mongodb_uri or settings.infra.mongodb_uri
        return MongoDBSaver.from_conn_string(uri, serde=serde)
    raise ValueError(f"Unsupported synchronous checkpointer backend: {backend!r}.")


async def build_async_checkpointer(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Any:
    """Build the configured asynchronous checkpointer."""
    backend = resolve_backend(settings.checkpointer, settings, prefer_async=True)
    serde = build_checkpointer_serde(settings, registry=registry)

    if backend == "none":
        return None
    if backend == "memory":
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver(serde=serde)
    if backend == "sqlite_async":
        path = _sqlite_path(settings.checkpointer.sqlite_path)
        return _open_async_sqlite_saver(path, serde)
    if backend == "postgres_async":
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        uri = settings.checkpointer.postgres_uri or settings.infra.postgres_uri
        return AsyncPostgresSaver.from_conn_string(uri, serde=serde)
    if backend == "redis_async":
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver

        url = settings.checkpointer.redis_url or settings.infra.redis_url
        return AsyncRedisSaver.from_conn_string(url)
    if backend == "mongodb_async":
        from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

        uri = settings.checkpointer.mongodb_uri or settings.infra.mongodb_uri
        return AsyncMongoDBSaver.from_conn_string(uri, serde=serde)
    raise ValueError(f"Unsupported asynchronous checkpointer backend: {backend!r}.")
