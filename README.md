# ooai-persistence

[![CI](https://github.com/pr1m8/ooai-persistence/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/ooai-persistence/actions/workflows/ci.yml)
[![Release](https://github.com/pr1m8/ooai-persistence/actions/workflows/release.yml/badge.svg)](https://github.com/pr1m8/ooai-persistence/actions/workflows/release.yml)
[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://pr1m8.github.io/ooai-persistence/)
![Python](https://img.shields.io/badge/python-3.13-blue)
![PDM](https://img.shields.io/badge/package%20manager-pdm-blue)
![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)
![Async Postgres](https://img.shields.io/badge/e2e-async%20postgres%20store%20%2B%20checkpointer-brightgreen)

`ooai-persistence` provides typed persistence helpers for LangGraph-based OOAI applications.

## Responsibilities

- checkpointer configuration and backend resolution
- store configuration and backend resolution
- graph cache configuration
- strict serializer allowlist support
- sync and async persistence contexts
- local infrastructure defaults for Postgres, optional Redis, and optional MongoDB

## Quick start

```bash
pdm install -G :all
pdm run pytest
pdm run ooai-persistence smoke --backend memory
```

## Pragmatic usage

Most applications want one of these patterns:

- open a managed persistence bundle and use the store directly
- compile a `StateGraph` with managed persistence already attached
- bind managed persistence onto a graph you already compiled elsewhere

For a no-infrastructure memory bundle:

```python
from ooai_persistence import AppSettings, open_sync_persistence

settings = AppSettings.memory()

with open_sync_persistence(settings) as persistence:
    persistence.store.put(("users", "will"), "profile", {"name": "Will"})
    profile = persistence.store.get(("users", "will"), "profile")
```

For a pragmatic LangGraph flow:

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from ooai_persistence import AppSettings, open_graph


class State(TypedDict):
    question: str
    answer: str


def respond(state: State) -> State:
    return {"answer": f"Echo: {state['question']}"}


graph = StateGraph(State)
graph.add_node("respond", respond)
graph.add_edge(START, "respond")
graph.add_edge("respond", END)

settings = AppSettings.local_sqlite(".ooai/persistence/dev.sqlite3")

async with open_graph(graph, settings) as runtime:
    await runtime.persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
    result = await runtime.graph.ainvoke({"question": "hello", "answer": ""})
```

If you already have a compiled graph, bind persistence onto it:

```python
from ooai_persistence import AppSettings, bind_graph_with_persistence, open_sync_persistence

compiled = graph.compile()

with open_sync_persistence(AppSettings.memory()) as bundle:
    persistent_graph = bind_graph_with_persistence(compiled, bundle)
```

## LangGraph wrappers

The top-level graph helpers are:

- `compile_graph_with_persistence(graph, bundle, **compile_kwargs)`
- `bind_graph_with_persistence(compiled_graph, bundle)`
- `open_sync_graph(graph_or_compiled_graph, settings, **compile_kwargs)`
- `open_graph(graph_or_compiled_graph, settings, **compile_kwargs)`

`open_sync_graph` and `open_graph` yield a `PersistentGraph` with:

- `runtime.graph`: the compiled or rebound LangGraph
- `runtime.persistence`: the managed `PersistenceBundle`

## CLI

The package ships a small diagnostics and smoke-test CLI:

```bash
ooai-persistence doctor --backend postgres --json
ooai-persistence smoke --backend memory
ooai-persistence smoke --backend sqlite --sqlite-path .ooai/persistence/smoke.sqlite3
ooai-persistence smoke --backend postgres --async
ooai-persistence env --output .env
ooai-persistence ensure-postgres
```

The async Postgres smoke command exercises both the LangGraph checkpointer and
store through the public context API.

## Local Postgres

```bash
make bootstrap
make infra-up
make infra-test-postgres
make infra-down
```

`make bootstrap` creates `.env` from `.env.example` when needed and installs all
PDM extras. See `infra/README.md` for Compose details.

`make infra-test-postgres` runs the real async Postgres E2E path and the CLI
smoke path against Docker Compose Postgres.

If Docker is not installed but `.env` points at a reachable Postgres server,
`make infra-up` falls back to `ooai-persistence ensure-postgres` and creates the
configured database if needed.

## Default backend behavior

By default, checkpointer and store use `backend="auto"`.

`auto` resolves in this order:
1. async Postgres when configured
2. async SQLite when configured
3. async MongoDB when configured
4. async Redis when configured
5. in-memory fallback

## Serializer allowlist registry

The package includes a reusable strict-msgpack registry:

```python
from ooai_persistence.serde.registry import MsgpackAllowlistRegistry

registry = MsgpackAllowlistRegistry()
registry.register_symbol("my_app.models", "WorkflowState")
registry.register_type(MyPersistedModel)
registry.register_import_string("my_app.models:AnotherPersistedModel")
```

That registry can be passed into the persistence context:

```python
from ooai_persistence import AppSettings, open_persistence

settings = AppSettings()

async with open_persistence(settings, registry=registry) as bundle:
    ...
```

The same registry also flows through `open_graph(...)` and `open_sync_graph(...)`.

## Documentation and release checks

```bash
pdm run sphinx-build -W -b html docs docs/_build/html
pdm build
```

CI runs formatting, linting, typing, tests with coverage, and the Sphinx build.
Docs also publish from `main` to [GitHub Pages](https://pr1m8.github.io/ooai-persistence/).

## Releasing

Releases are tag-driven:

```bash
pdm lock --check
make check
git tag v0.2.2
git push origin v0.2.2
```

The release workflow verifies that the tag matches `pyproject.toml`, runs the
async Postgres E2E checks, builds the wheel/sdist, publishes through PyPI
Trusted Publishing, and creates a GitHub Release with artifacts attached.
