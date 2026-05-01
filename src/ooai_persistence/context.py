"""Context managers for persistence resources."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager

from ooai_persistence.bootstrap import maybe_async_setup, maybe_setup, should_setup_for_resource
from ooai_persistence.resources import (
    PersistenceBundle,
    build_async_persistence_bundle,
    build_persistence_bundle,
)
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings


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


open_persistence = async_persistence_context
open_sync_persistence = persistence_context
