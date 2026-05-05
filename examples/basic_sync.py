"""Pragmatic sync LangGraph example for ``ooai_persistence``."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ooai_persistence import open_sync_graph, sqlite_settings


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


def main() -> None:
    """Compile a graph with managed persistence and use the store directly."""
    settings = sqlite_settings(".ooai/persistence/dev.sqlite3")
    with open_sync_graph(build_graph(), settings) as runtime:
        store = runtime.persistence.store
        assert store is not None
        store.put(("profiles", "demo"), "name", {"value": "Will"})
        result = runtime.graph.invoke(
            {"question": "hello", "answer": ""},
            config={"configurable": {"thread_id": "demo-thread"}},
        )
        print(result)
        print(store.get(("profiles", "demo"), "name"))


if __name__ == "__main__":
    main()
