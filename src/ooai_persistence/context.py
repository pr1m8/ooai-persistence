"""Context managers for persistence resources."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

from ooai_persistence.bootstrap import maybe_async_setup, maybe_setup, should_setup_for_resource
from ooai_persistence.resources import (
    PersistenceBundle,
    build_async_persistence_bundle,
    build_persistence_bundle,
)
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import (
    AppSettings,
    memory_settings,
    postgres_settings,
    sqlite_settings,
)


def _store_only_settings(settings: AppSettings) -> AppSettings:
    """Return a copy of settings with only the store resource enabled."""
    return settings.model_copy(
        update={
            "checkpointer": settings.checkpointer.model_copy(update={"backend": "none"}),
            "graph_cache": settings.graph_cache.model_copy(
                update={"enabled": False, "backend": "none"}
            ),
        }
    )


def _postgres_open_settings(
    uri: str | None,
    *,
    host: str | None,
    port: int | None,
    database: str | None,
    user: str | None,
    password: str | None,
    sslmode: str | None,
    graph_cache: bool,
) -> AppSettings:
    """Resolve Postgres helper defaults from environment-backed app settings."""
    if uri is not None:
        return postgres_settings(uri, graph_cache=graph_cache)

    defaults = AppSettings().infra
    return postgres_settings(
        host=host if host is not None else defaults.postgres_host,
        port=port if port is not None else defaults.postgres_port,
        database=database if database is not None else defaults.postgres_database,
        user=user if user is not None else defaults.postgres_user,
        password=(
            password if password is not None else defaults.postgres_password.get_secret_value()
        ),
        sslmode=sslmode if sslmode is not None else defaults.postgres_sslmode,
        graph_cache=graph_cache,
    )


@contextmanager
def persistence_context(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Iterator[PersistenceBundle]:
    """Yield a synchronous persistence bundle with managed cleanup."""
    bundle = build_persistence_bundle(settings, registry=registry)
    with ExitStack() as stack:
        for field_name in ("checkpointer", "store"):
            resource = getattr(bundle, field_name)
            if (
                resource is not None
                and hasattr(resource, "__enter__")
                and hasattr(resource, "__exit__")
            ):
                setattr(bundle, field_name, stack.enter_context(resource))
        maybe_setup(
            bundle.checkpointer,
            enabled=should_setup_for_resource(settings, settings.checkpointer),
        )
        maybe_setup(
            bundle.store,
            enabled=should_setup_for_resource(settings, settings.store),
        )
        yield bundle


@asynccontextmanager
async def async_persistence_context(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> AsyncIterator[PersistenceBundle]:
    """Yield an asynchronous persistence bundle with managed cleanup."""
    bundle = await build_async_persistence_bundle(settings, registry=registry)
    async with AsyncExitStack() as stack:
        for field_name in ("checkpointer", "store"):
            resource = getattr(bundle, field_name)
            if (
                resource is not None
                and hasattr(resource, "__aenter__")
                and hasattr(resource, "__aexit__")
            ):
                setattr(bundle, field_name, await stack.enter_async_context(resource))
        await maybe_async_setup(
            bundle.checkpointer,
            enabled=should_setup_for_resource(settings, settings.checkpointer),
        )
        await maybe_async_setup(
            bundle.store,
            enabled=should_setup_for_resource(settings, settings.store),
        )
        yield bundle


@contextmanager
def open_sync_memory_persistence(
    *,
    graph_cache: bool = True,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Iterator[PersistenceBundle]:
    """Open a synchronous in-memory persistence bundle."""
    with persistence_context(memory_settings(graph_cache=graph_cache), registry=registry) as bundle:
        yield bundle


@contextmanager
def open_sync_sqlite_persistence(
    path: str | Path = ".ooai/persistence/persistence.sqlite3",
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Iterator[PersistenceBundle]:
    """Open a synchronous SQLite-backed persistence bundle."""
    with persistence_context(sqlite_settings(path), registry=registry) as bundle:
        yield bundle


@contextmanager
def open_sync_postgres_persistence(
    uri: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
    sslmode: str | None = None,
    graph_cache: bool = True,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Iterator[PersistenceBundle]:
    """Open a synchronous Postgres-backed persistence bundle."""
    settings = _postgres_open_settings(
        uri,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode=sslmode,
        graph_cache=graph_cache,
    )
    with persistence_context(settings, registry=registry) as bundle:
        yield bundle


@asynccontextmanager
async def open_memory_persistence(
    *,
    graph_cache: bool = True,
    registry: MsgpackAllowlistRegistry | None = None,
) -> AsyncIterator[PersistenceBundle]:
    """Open an asynchronous in-memory persistence bundle."""
    async with async_persistence_context(
        memory_settings(graph_cache=graph_cache),
        registry=registry,
    ) as bundle:
        yield bundle


@asynccontextmanager
async def open_sqlite_persistence(
    path: str | Path = ".ooai/persistence/persistence.sqlite3",
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> AsyncIterator[PersistenceBundle]:
    """Open an asynchronous SQLite-backed persistence bundle."""
    async with async_persistence_context(sqlite_settings(path), registry=registry) as bundle:
        yield bundle


@asynccontextmanager
async def open_postgres_persistence(
    uri: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
    sslmode: str | None = None,
    graph_cache: bool = True,
    registry: MsgpackAllowlistRegistry | None = None,
) -> AsyncIterator[PersistenceBundle]:
    """Open an asynchronous Postgres-backed persistence bundle."""
    settings = _postgres_open_settings(
        uri,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode=sslmode,
        graph_cache=graph_cache,
    )
    async with async_persistence_context(settings, registry=registry) as bundle:
        yield bundle


@contextmanager
def store_context(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> Iterator[Any]:
    """Yield only the configured synchronous store resource."""
    with persistence_context(_store_only_settings(settings), registry=registry) as bundle:
        if bundle.store is None:
            raise ValueError("Store backend resolved to none.")
        yield bundle.store


@asynccontextmanager
async def async_store_context(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
) -> AsyncIterator[Any]:
    """Yield only the configured asynchronous store resource."""
    async with async_persistence_context(
        _store_only_settings(settings),
        registry=registry,
    ) as bundle:
        if bundle.store is None:
            raise ValueError("Store backend resolved to none.")
        yield bundle.store


@contextmanager
def open_sync_memory_store() -> Iterator[Any]:
    """Open a synchronous in-memory store."""
    with store_context(memory_settings()) as store:
        yield store


@contextmanager
def open_sync_sqlite_store(
    path: str | Path = ".ooai/persistence/persistence.sqlite3",
) -> Iterator[Any]:
    """Open a synchronous SQLite-backed store."""
    with store_context(sqlite_settings(path)) as store:
        yield store


@contextmanager
def open_sync_postgres_store(
    uri: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
    sslmode: str | None = None,
) -> Iterator[Any]:
    """Open a synchronous Postgres-backed store."""
    with store_context(
        _postgres_open_settings(
            uri,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode,
            graph_cache=True,
        )
    ) as store:
        yield store


@asynccontextmanager
async def open_memory_store() -> AsyncIterator[Any]:
    """Open an asynchronous in-memory store."""
    async with async_store_context(memory_settings()) as store:
        yield store


@asynccontextmanager
async def open_sqlite_store(
    path: str | Path = ".ooai/persistence/persistence.sqlite3",
) -> AsyncIterator[Any]:
    """Open an asynchronous SQLite-backed store."""
    async with async_store_context(sqlite_settings(path)) as store:
        yield store


@asynccontextmanager
async def open_postgres_store(
    uri: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
    sslmode: str | None = None,
) -> AsyncIterator[Any]:
    """Open an asynchronous Postgres-backed store."""
    async with async_store_context(
        _postgres_open_settings(
            uri,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode,
            graph_cache=True,
        )
    ) as store:
        yield store


open_persistence = async_persistence_context
open_sync_persistence = persistence_context
open_store = async_store_context
open_sync_store = store_context
