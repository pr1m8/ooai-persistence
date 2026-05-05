"""Pragmatic async LangGraph example for ``ooai_persistence``."""

from __future__ import annotations

import asyncio
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ooai_persistence import AppSettings, open_graph


class State(TypedDict):
    question: str
    answer: str


def respond(state: State) -> State:
    return {"question": state["question"], "answer": f"Echo: {state['question']}"}


def build_graph() -> StateGraph[State, None, State, State]:
    graph = StateGraph(State)
    graph.add_node("respond", respond)
    graph.add_edge(START, "respond")
    graph.add_edge("respond", END)
    return graph


async def main() -> None:
    """Compile a graph with managed async persistence and use the async store."""
    settings = AppSettings.local_sqlite(".ooai/persistence/dev.sqlite3")
    async with open_graph(build_graph(), settings) as runtime:
        store = runtime.persistence.store
        assert store is not None
        await store.aput(("profiles", "demo"), "name", {"value": "Will"})
        result = await runtime.graph.ainvoke({"question": "hello", "answer": ""})
        print(result)
        print(await store.aget(("profiles", "demo"), "name"))


if __name__ == "__main__":
    asyncio.run(main())
