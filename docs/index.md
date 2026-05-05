# ooai-persistence

Typed persistence helpers for LangGraph-based OOAI applications.

## Start here

The usual entrypoints are:

- `memory_settings()` for tests and no-infra runs
- `sqlite_settings(path)` for one-file local persistence
- `postgres_settings(...)` for the real async Postgres path

```python
from ooai_persistence import memory_settings, postgres_settings, sqlite_settings

memory = memory_settings()
sqlite = sqlite_settings(".ooai/persistence/dev.sqlite3")
postgres = postgres_settings(database="ooai_persistence")
```

```python
from ooai_persistence import open_sync_persistence, sqlite_settings

settings = sqlite_settings(".ooai/persistence/dev.sqlite3")

with open_sync_persistence(settings) as persistence:
    checkpointer = persistence.checkpointer
    store = persistence.store
    graph_cache = persistence.graph_cache
```

## Pragmatic patterns

The most useful entrypoints are:

- `open_sync_persistence(...)` and `open_persistence(...)` when you want raw store/checkpointer access
- `open_sync_graph(...)` and `open_graph(...)` when you want a compiled LangGraph plus managed persistence
- `bind_graph_with_persistence(...)` when the graph is already compiled somewhere else

## Install

```bash
pdm install -G :all
```

Backend extras are available for Postgres, SQLite, Redis, MongoDB, LangSmith,
and docs:

```bash
pdm add "ooai-persistence[postgres]"
pdm add "ooai-persistence[sqlite]"
```

## Configuration

Use `AppSettings` directly, or load settings from `.env` with the
`OOAI_PERSISTENCE_` prefix.

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from ooai_persistence import open_graph, postgres_settings


class State(TypedDict):
    question: str
    answer: str


def respond(state: State) -> State:
    return {"answer": f"Echo: {state['question']}"}


graph = StateGraph(State)
graph.add_node("respond", respond)
graph.add_edge(START, "respond")
graph.add_edge("respond", END)

settings = postgres_settings(database="ooai_persistence")

async with open_graph(graph, settings) as runtime:
    await runtime.persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
    result = await runtime.graph.ainvoke(
        {"question": "hello", "answer": ""},
        config={"configurable": {"thread_id": "demo-thread"}},
    )
```

Checkpointed graph runs need a runnable config such as
`{"configurable": {"thread_id": "demo-thread"}}`.

LangSmith settings read standard `LANGSMITH_*` variables:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=ooai
```

## Local Infrastructure

```bash
make bootstrap
make infra-up
make infra-test-postgres
make infra-down
```

See `infra/README.md` for Docker Compose details.

## CLI Smoke Checks

```bash
ooai-persistence doctor --backend postgres --json
ooai-persistence smoke --backend memory
ooai-persistence smoke --backend sqlite --sqlite-path .ooai/persistence/smoke.sqlite3
ooai-persistence smoke --backend postgres --async
```

The Postgres smoke path opens async LangGraph checkpointer and store resources,
runs setup, and verifies real round trips.

## Existing compiled graphs

```python
from ooai_persistence import bind_graph_with_persistence, memory_settings, open_sync_persistence

compiled = graph.compile()

with open_sync_persistence(memory_settings()) as bundle:
    persistent_graph = bind_graph_with_persistence(compiled, bundle)
    result = persistent_graph.invoke(
        {"question": "hello", "answer": ""},
        config={"configurable": {"thread_id": "demo-thread"}},
    )
```

## API Reference

```{eval-rst}
.. autosummary::
   :toctree: api
   :recursive:

   ooai_persistence
   ooai_persistence.settings
   ooai_persistence.context
   ooai_persistence.graphs
   ooai_persistence.resources
   ooai_persistence.registry
   ooai_persistence.serde.registry
```
