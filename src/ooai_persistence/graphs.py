"""Helpers for wiring persistence bundles into LangGraph graphs."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ooai_persistence.context import async_persistence_context, persistence_context
from ooai_persistence.resources import PersistenceBundle
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph, StateGraph


@dataclass(slots=True)
class PersistentGraph:
    """A compiled graph plus the managed persistence resources it uses."""

    graph: Any
    persistence: PersistenceBundle


def compile_graph_with_persistence(
    graph: StateGraph[Any, Any, Any, Any] | Any,
    bundle: PersistenceBundle,
    **compile_kwargs: Any,
) -> CompiledStateGraph[Any, Any, Any, Any] | Any:
    """Compile a StateGraph with the provided persistence bundle."""
    if not hasattr(graph, "compile"):
        raise TypeError("compile_graph_with_persistence expects a LangGraph StateGraph.")
    return graph.compile(
        checkpointer=bundle.checkpointer,
        store=bundle.store,
        cache=bundle.graph_cache,
        **compile_kwargs,
    )


def bind_graph_with_persistence(
    graph: Any,
    bundle: PersistenceBundle,
) -> Any:
    """Return a compiled graph copy that uses the provided persistence bundle."""
    if not hasattr(graph, "copy"):
        raise TypeError("bind_graph_with_persistence expects a compiled LangGraph.")
    return cast(Any, graph).copy(
        update={
            "checkpointer": bundle.checkpointer,
            "store": bundle.store,
            "cache": bundle.graph_cache,
        }
    )


@contextmanager
def open_sync_graph(
    graph: StateGraph[Any, Any, Any, Any] | Any,
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
    **compile_kwargs: Any,
) -> Iterator[PersistentGraph]:
    """Open sync persistence and return a compiled or rebound graph."""
    with persistence_context(settings, registry=registry) as bundle:
        resolved_graph = _resolve_graph(graph, bundle, compile_kwargs)
        yield PersistentGraph(graph=resolved_graph, persistence=bundle)


@asynccontextmanager
async def open_graph(
    graph: StateGraph[Any, Any, Any, Any] | Any,
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
    **compile_kwargs: Any,
) -> AsyncIterator[PersistentGraph]:
    """Open async persistence and return a compiled or rebound graph."""
    async with async_persistence_context(settings, registry=registry) as bundle:
        resolved_graph = _resolve_graph(graph, bundle, compile_kwargs)
        yield PersistentGraph(graph=resolved_graph, persistence=bundle)


def _resolve_graph(
    graph: Any,
    bundle: PersistenceBundle,
    compile_kwargs: dict[str, Any],
) -> Any:
    if hasattr(graph, "compile"):
        return compile_graph_with_persistence(graph, bundle, **compile_kwargs)
    if compile_kwargs:
        raise TypeError("compile kwargs are only supported when passing a StateGraph.")
    return bind_graph_with_persistence(graph, bundle)
