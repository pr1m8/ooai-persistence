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

## What this package adds

This package gives an agent or LangGraph application a reusable persistence
layer with:

- a long-term store
- a LangGraph-compatible checkpointer
- an optional graph cache
- typed settings and env resolution
- direct-open sync and async helpers
- Postgres, SQLite, and memory backends
- E2E-tested public entrypoints

The useful mental model is:

- `store`: durable application or user memory
- `checkpointer`: graph/thread execution state
- `graph_cache`: optional caching
- helpers: one place to bootstrap all of that cleanly

## What the E2E coverage means

The E2E suite exercises the package the way an application would actually use
it:

- open persistence through the public helpers
- write and read store values
- save and load checkpoints
- run async Postgres smoke checks
- verify the `make up -> make test-e2e-postgres -> make down` developer flow

So the package is not only unit-tested internally; the public API paths are
checked end to end as well.

## Using it in an agent package

If you are building an agent package, keep persistence setup in one small
module and let the rest of the app depend on that.

### Store-only bootstrap

Use this when you only need durable memory:

```python
from ooai_persistence import open_postgres_store


async def save_profile() -> None:
    async with open_postgres_store() as store:
        await store.aput(("users", "will"), "profile", {"name": "Will"})
```

### Full persistence bootstrap

Use this when you need both durable storage and checkpointing:

```python
from ooai_persistence import open_postgres_persistence


async def run_agent() -> None:
    async with open_postgres_persistence() as persistence:
        await persistence.store.aput(("users", "will"), "profile", {"name": "Will"})
        checkpointer = persistence.checkpointer
```

### LangGraph bootstrap

Use this when your package compiles and runs LangGraph graphs directly:

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from ooai_persistence import open_graph, postgres_settings


class State(TypedDict):
    message: str
    reply: str


def respond(state: State) -> State:
    return {"reply": f"Echo: {state['message']}"}


graph = StateGraph(State)
graph.add_node("respond", respond)
graph.add_edge(START, "respond")
graph.add_edge("respond", END)


async def run_agent_graph() -> None:
    async with open_graph(graph, postgres_settings()) as runtime:
        result = await runtime.graph.ainvoke(
            {"message": "hi", "reply": ""},
            config={"configurable": {"thread_id": "demo-thread"}},
        )
```

That keeps persistence concerns out of the rest of the agent package and gives
you one place to swap memory, SQLite, local Postgres, or hosted Postgres.

## LangSmith integration

This package is not your tracing backend, but it keeps LangSmith-related
settings nearby so persistence and tracing can bootstrap together.

It reads the standard LangSmith environment variables:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=ooai
LANGSMITH_ENDPOINT=
```

A practical split in an agent package is:

- `ooai-persistence` for store, checkpointing, and graph cache
- LangSmith env vars for tracing
- your own runtime package for orchestration and business logic

That usually keeps the boundaries clean.

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
make up
make test-e2e-postgres
make down
```

Or, with the explicit infra names:

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
make up
make test-e2e-postgres
make down
```

Or use the explicit infra variants:

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

`make up` and `make down` are the short aliases for that workflow.

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

That makes hosted Postgres and Supabase-style setups easy to bootstrap in agent
packages without custom config translation layers.

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

The repository also includes a `.readthedocs.yaml` config so the same Sphinx
docs can be built by Read the Docs after the project is imported there. GitHub
Pages is the currently active published docs target in this repository.

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
