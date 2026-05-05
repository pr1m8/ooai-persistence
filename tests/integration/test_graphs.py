"""Integration tests for LangGraph convenience wrappers."""

from __future__ import annotations

from typing import TypedDict

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from ooai_persistence import (
    AppSettings,
    bind_graph_with_persistence,
    compile_graph_with_persistence,
    open_graph,
    open_sync_graph,
    open_sync_persistence,
)


class State(TypedDict):
    count: int


def increment(state: State) -> State:
    return {"count": state["count"] + 1}


def build_graph() -> StateGraph[State, None, State, State]:
    graph = StateGraph(State)
    graph.add_node("increment", increment)
    graph.add_edge(START, "increment")
    graph.add_edge("increment", END)
    return graph


CONFIG: RunnableConfig = {"configurable": {"thread_id": "test-thread"}}


@pytest.mark.integration
def test_compile_graph_with_persistence_memory() -> None:
    graph = build_graph()
    settings = AppSettings.memory()

    with open_sync_persistence(settings) as bundle:
        compiled = compile_graph_with_persistence(graph, bundle)

        assert compiled.checkpointer is bundle.checkpointer
        assert compiled.store is bundle.store
        assert compiled.cache is bundle.graph_cache
        assert compiled.invoke({"count": 1}, config=CONFIG) == {"count": 2}


@pytest.mark.integration
def test_bind_graph_with_persistence_memory() -> None:
    graph = build_graph().compile()
    settings = AppSettings.memory()

    with open_sync_persistence(settings) as bundle:
        compiled = bind_graph_with_persistence(graph, bundle)

        assert compiled.checkpointer is bundle.checkpointer
        assert compiled.store is bundle.store
        assert compiled.cache is bundle.graph_cache
        assert compiled.invoke({"count": 2}, config=CONFIG) == {"count": 3}


@pytest.mark.integration
def test_open_sync_graph_wraps_graph_and_bundle() -> None:
    settings = AppSettings.memory()

    with open_sync_graph(build_graph(), settings) as runtime:
        assert runtime.graph.checkpointer is runtime.persistence.checkpointer
        assert runtime.graph.invoke({"count": 3}, config=CONFIG) == {"count": 4}


@pytest.mark.integration
async def test_open_graph_wraps_async_bundle() -> None:
    settings = AppSettings.memory()

    async with open_graph(build_graph(), settings) as runtime:
        assert runtime.graph.store is runtime.persistence.store
        assert await runtime.graph.ainvoke({"count": 4}, config=CONFIG) == {"count": 5}


def test_open_graph_rejects_compile_kwargs_for_compiled_graph() -> None:
    settings = AppSettings.memory()

    with (
        pytest.raises(TypeError, match="compile kwargs"),
        open_sync_graph(
            build_graph().compile(),
            settings,
            name="already-compiled",
        ),
    ):
        pass
