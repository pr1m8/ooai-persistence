# ooai-persistence

Typed persistence helpers for LangGraph-based OOAI applications.

```python
from ooai_persistence import AppSettings, open_sync_persistence

settings = AppSettings.memory()

with open_sync_persistence(settings) as persistence:
    checkpointer = persistence.checkpointer
    store = persistence.store
    graph_cache = persistence.graph_cache
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
from ooai_persistence import AppSettings, open_persistence

settings = AppSettings.local_sqlite(".ooai/persistence/dev.sqlite3")

async with open_persistence(settings) as persistence:
    ...
```

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

## API Reference

```{eval-rst}
.. autosummary::
   :toctree: api
   :recursive:

   ooai_persistence
   ooai_persistence.settings
   ooai_persistence.context
   ooai_persistence.resources
   ooai_persistence.registry
   ooai_persistence.serde.registry
```
