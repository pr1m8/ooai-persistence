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

If you do not want to touch settings at all, open the bundle directly:

```python
from ooai_persistence import open_postgres_persistence

async with open_postgres_persistence(database="ooai_persistence") as persistence:
    await persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
```

If you only want the store, you can open just that resource:

```python
from ooai_persistence import open_postgres_store

async with open_postgres_store(database="ooai_persistence") as store:
    await store.aput(("profiles", "demo"), "name", {"value": "Will"})
```

## What this package adds

`ooai-persistence` gives agent packages and LangGraph apps a reusable
persistence layer with:

- a long-term store
- a LangGraph-compatible checkpointer
- an optional graph cache
- typed settings and env resolution
- direct-open sync and async helpers

The public API is designed so most applications can start from a store-only
helper, a full persistence helper, or a graph helper, instead of hand-building
nested settings.

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
- `open_sync_memory_persistence(...)`, `open_sqlite_persistence(...)`, and `open_postgres_persistence(...)` when you want that access without building settings first
- `open_sync_store(...)` and `open_store(...)` when you only want the long-term store
- `open_sync_graph(...)` and `open_graph(...)` when you want a compiled LangGraph plus managed persistence
- `bind_graph_with_persistence(...)` when the graph is already compiled somewhere else

## Agent package pattern

If you are building an agent package, keep persistence setup in one small
module and let the rest of the application depend on that boundary.

Store-only usage:

```python
from ooai_persistence import open_postgres_store

async with open_postgres_store() as store:
    await store.aput(("users", "will"), "profile", {"name": "Will"})
```

Full persistence usage:

```python
from ooai_persistence import open_postgres_persistence

async with open_postgres_persistence() as persistence:
    await persistence.store.aput(("users", "will"), "profile", {"name": "Will"})
```

LangGraph usage:

```python
from ooai_persistence import open_graph, postgres_settings

settings = postgres_settings()
```

Checkpointed LangGraph runs still need a runnable config like:

```python
config={"configurable": {"thread_id": "demo-thread"}}
```

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

This package is not your tracing backend, but it keeps LangSmith settings close
to persistence bootstrap so agent packages can configure both together without
scattering that setup across modules.

## Local Infrastructure

```bash
make bootstrap
make up
make test-e2e-postgres
make down
```

See `infra/README.md` for Docker Compose details.

The repository also includes `.readthedocs.yaml`, so the same Sphinx docs can
be built by Read the Docs after project activation. GitHub Pages is the
currently active docs deployment target.

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
