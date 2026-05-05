# ooai-persistence

[![CI](https://github.com/pr1m8/ooai-persistence/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/ooai-persistence/actions/workflows/ci.yml)
[![Release](https://github.com/pr1m8/ooai-persistence/actions/workflows/release.yml/badge.svg)](https://github.com/pr1m8/ooai-persistence/actions/workflows/release.yml)
[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://pr1m8.github.io/ooai-persistence/)
![Python](https://img.shields.io/badge/python-3.13-blue)
![PDM](https://img.shields.io/badge/package%20manager-pdm-blue)
![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)
![Async Postgres](https://img.shields.io/badge/e2e-async%20postgres%20store%20%2B%20checkpointer-brightgreen)

`ooai-persistence` gives LangGraph apps a usable persistence layer without
making you hand-build a big settings tree first.

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

## Start here

Most applications should start with one of these helpers:

- `memory_settings()` for tests and local no-infra runs
- `sqlite_settings(path)` for one-file local persistence
- `postgres_settings(...)` for the real async Postgres path

```python
from ooai_persistence import memory_settings, postgres_settings, sqlite_settings

memory = memory_settings()
sqlite = sqlite_settings(".ooai/persistence/dev.sqlite3")
postgres = postgres_settings(database="ooai_persistence")
postgres_via_uri = postgres_settings("postgresql://postgres:postgres@localhost:5442/ooai_persistence?sslmode=disable")
```

If those cover your case, you do not need to construct `AppSettings(...)`
directly.

If you want the shortest possible path, skip settings entirely and open the
bundle directly:

```python
from ooai_persistence import (
    open_memory_persistence,
    open_postgres_persistence,
    open_sqlite_persistence,
)

async with open_postgres_persistence(database="ooai_persistence") as persistence:
    await persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
```

That is the easiest async entrypoint in the package right now.

If you only want the long-term store and not the full persistence bundle:

```python
from ooai_persistence import open_postgres_store

async with open_postgres_store(database="ooai_persistence") as store:
    await store.aput(("profiles", "demo"), "name", {"value": "Will"})
    item = await store.aget(("profiles", "demo"), "name")
```

## Common patterns

### 1. Use the store directly

```python
from ooai_persistence import open_sync_memory_store

with open_sync_memory_store() as store:
    store.put(("users", "will"), "profile", {"name": "Will"})
    profile = store.get(("users", "will"), "profile")
```

### 2. Compile a graph with async persistence attached

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

settings = postgres_settings(
    host="localhost",
    port=5442,
    database="ooai_persistence",
    user="postgres",
    password="postgres",
)

async with open_graph(graph, settings) as runtime:
    await runtime.persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
    result = await runtime.graph.ainvoke(
        {"question": "hello", "answer": ""},
        config={"configurable": {"thread_id": "demo-thread"}},
    )
```

When a graph uses a checkpointer, LangGraph expects a `configurable.thread_id`
or another checkpoint key in the runnable config.

### 3. Bind persistence onto a compiled graph

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

## Async Postgres, the easy way

If your real target is async Postgres, the shortest path is:

```python
from ooai_persistence import open_postgres_persistence

async with open_postgres_persistence(database="ooai_persistence") as persistence:
    await persistence.store.aput(("profiles", "demo"), "name", {"value": "Will"})
```

If you are compiling a LangGraph too:

```python
from ooai_persistence import open_graph, postgres_settings

settings = postgres_settings(database="ooai_persistence")
```

Or use a URI:

```python
from ooai_persistence import open_postgres_persistence

async with open_postgres_persistence(
    "postgresql://postgres:postgres@localhost:5442/ooai_persistence?sslmode=disable"
) as persistence:
    ...
```

If you call the Postgres helpers without connection arguments, they read the
same `OOAI_PERSISTENCE_INFRA__POSTGRES_*` settings that `AppSettings()` uses.

Then bring Postgres up locally:

```bash
make bootstrap
make infra-up
make infra-test-postgres
```

That path exercises the real async LangGraph checkpointer and store, not a fake
shim around them.

## LangGraph wrappers

The top-level graph helpers are:

- `compile_graph_with_persistence(graph, bundle, **compile_kwargs)`
- `bind_graph_with_persistence(compiled_graph, bundle)`
- `open_sync_graph(graph_or_compiled_graph, settings, **compile_kwargs)`
- `open_graph(graph_or_compiled_graph, settings, **compile_kwargs)`

The top-level persistence helpers are:

- `open_sync_memory_persistence()`
- `open_sync_sqlite_persistence(path)`
- `open_sync_postgres_persistence(...)`
- `open_memory_persistence()`
- `open_sqlite_persistence(path)`
- `open_postgres_persistence(...)`

The top-level store-only helpers are:

- `open_sync_store(settings)`
- `open_sync_memory_store()`
- `open_sync_sqlite_store(path)`
- `open_sync_postgres_store(...)`
- `open_store(settings)`
- `open_memory_store()`
- `open_sqlite_store(path)`
- `open_postgres_store(...)`

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
make infra-up-docker
make infra-test-postgres
make infra-down
```

`make bootstrap` creates `.env` from `.env.example` when needed and installs all
PDM extras. See `infra/README.md` for Compose details.

`make infra-test-postgres` remains as a compatibility alias for the same
Postgres E2E and CLI smoke flow.

If you want the shortest test commands, use:

```bash
make test-e2e-memory
make test-e2e-sqlite
make test-e2e-local
make test-e2e-postgres
```

The Postgres target brings up the configured database, runs the public wrapper
E2E suite for `open_postgres_persistence(...)` and `open_postgres_store(...)`,
and then runs the async CLI smoke check.

`make infra-up` is the ergonomic default: it uses the Postgres server from
`.env`, ensures the configured database exists, and avoids depending on Docker
just to run the async store and persistence tests locally.

If you want the Compose-backed service explicitly, use `make infra-up-docker`.

The package also accepts standard Postgres env names when you do not want the
full nested prefix, including:

- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` / `POSTGRES_DATABASE`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SSLMODE`
- `POSTGRES_POOL_MIN_SIZE`, `POSTGRES_POOL_MAX_SIZE`
- `DATABASE_URL`, `POSTGRES_URL`, `POSTGRES_URI`
- `SUPABASE_DB_URL`, `SUPABASE_DATABASE_URL`

That means the zero-argument Postgres helpers can work cleanly in plain
Postgres or Supabase-style environments:

```python
from ooai_persistence import open_postgres_store

async with open_postgres_store() as store:
    ...
```

The matching `.env` path is already laid out in [.env.example](/Users/will/Projects/ooai-persistence/.env.example).

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
It also flows through the direct-open helpers like `open_postgres_persistence(...)`.

## When to use AppSettings directly

Reach for `AppSettings(...)` only when you want to:

- override checkpointer and store backends separately
- drive config from `.env`
- customize serializer allowlists, cache settings, or infra defaults
- compose persistence settings into a larger application settings object

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
git tag vX.Y.Z
git push origin vX.Y.Z
```

The release workflow verifies that the tag matches `pyproject.toml`, runs the
async Postgres E2E checks, builds the wheel/sdist, publishes through PyPI
Trusted Publishing, and creates a GitHub Release with artifacts attached.
