# AGENTS.md

## Purpose

`ooai-persistence` is the persistence layer for OOAI and LangGraph-based
applications.

This repository owns:

- persistence settings and env resolution
- serializer hardening and allowlist behavior
- store, checkpointer, and graph-cache resource construction
- sync and async context managers
- ergonomic direct-open helpers for store and persistence usage
- local Postgres-oriented testing and release verification

This repository does **not** own:

- model or provider selection logic
- runtime/session composition outside persistence concerns
- application-specific business workflows

Those should stay in sibling packages such as `ooai-llm` and `ooai-runtime`.

## How The Package Is Meant To Be Used

Most callers should start with one of three usage shapes:

1. Settings preset:
   - `memory_settings()`
   - `sqlite_settings(path)`
   - `postgres_settings(...)`

2. Direct persistence bundle:
   - `open_memory_persistence()`
   - `open_sqlite_persistence(path)`
   - `open_postgres_persistence(...)`

3. Store-only direct usage:
   - `open_memory_store()`
   - `open_sqlite_store(path)`
   - `open_postgres_store(...)`

For LangGraph-specific flows, use:

- `open_graph(...)`
- `open_sync_graph(...)`
- `bind_graph_with_persistence(...)`
- `compile_graph_with_persistence(...)`

Prefer the ergonomic top-level helpers over manually building nested settings
unless the change specifically concerns configuration behavior.

## Architecture

Important modules:

- `src/ooai_persistence/settings.py`
  - typed settings
  - env handling
  - preset constructors
- `src/ooai_persistence/context.py`
  - sync/async context managers
  - direct-open helpers
  - store-only wrappers
- `src/ooai_persistence/graphs.py`
  - LangGraph compile/bind helpers
- `src/ooai_persistence/providers/checkpointer.py`
  - checkpointer backend builders
- `src/ooai_persistence/providers/store.py`
  - store backend builders
- `src/ooai_persistence/providers/cache.py`
  - graph cache backend builders
- `src/ooai_persistence/smoke.py`
  - public API smoke test helpers
- `src/ooai_persistence/cli.py`
  - diagnostics and smoke CLI

Design constraints:

- keep optional backend imports lazy
- keep store/checkpointer/cache responsibilities separate
- keep serializer strictness as a first-class concern
- prefer typed configuration over ad hoc dicts
- preserve compatibility with real LangGraph backends, not mock-only flows

## Environment Model

The package supports both nested OOAI-style env vars and plain Postgres-style
env vars.

Primary nested env names:

- `OOAI_PERSISTENCE_INFRA__POSTGRES_HOST`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_PORT`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_DATABASE`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_USER`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_PASSWORD`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_SSLMODE`

Also supported:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_DATABASE`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_SSLMODE`
- `POSTGRES_POOL_MIN_SIZE`
- `POSTGRES_POOL_MAX_SIZE`
- `DATABASE_URL`
- `POSTGRES_URL`
- `POSTGRES_URI`
- `SUPABASE_DB_URL`
- `SUPABASE_DATABASE_URL`

Important behavior:

- zero-argument Postgres helpers should honor env-backed defaults
- standard DB URL aliases should map cleanly into both store and checkpointer
  Postgres config
- store pool settings currently apply to the Postgres store builders
- do not silently reintroduce hardcoded host/port defaults that bypass env
  resolution

## Tooling

Use PDM for everything in this repository.

Common commands:

```bash
pdm install -G :all
pdm run pytest
pdm run pyright
pdm run ruff check src tests examples
```

If dependency state may be wrong:

```bash
pdm install -G :all
```

If lock state or dependency constraints change:

```bash
pdm lock
```

## Make Targets

Preferred local flow:

```bash
make bootstrap
make up
make test-e2e-postgres
make down
```

Meaning:

- `make up`
  - uses the configured Postgres target
  - ensures the configured database exists
- `make test-e2e-postgres`
  - runs the real Postgres public-API E2E suite
  - runs the async smoke path
- `make down`
  - tears down compose-managed services when Docker is actually available
  - exits cleanly when Docker is unavailable

Other useful targets:

- `make check`
- `make test-e2e-local`
- `make test-e2e-memory`
- `make test-e2e-sqlite`
- `make infra-up-docker`
- `make docs`

## Testing Expectations

Use this test pyramid:

- unit tests:
  - settings resolution
  - env alias handling
  - provider selection
  - serializer logic
- integration tests:
  - sync/async memory flows
  - graph wrapper integration
- E2E tests:
  - public entrypoints
  - wrapper helpers
  - realistic Postgres flows

When changing Postgres ergonomics, verify at least:

```bash
make test-e2e-postgres
```

When changing core settings or public API shape, verify:

```bash
make check
```

## Documentation Expectations

When public API behavior changes, update:

- `README.md`
- `docs/index.md` when the user-facing workflow changes materially
- doc references for new public helpers if needed

The README should stay pragmatic:

- lead with the easiest working path
- show async Postgres clearly
- document store-only usage separately from full persistence bundles
- keep examples aligned with the actual public API

## Release Expectations

Versioning is tag-driven.

Before release:

```bash
make check
make test-e2e-postgres
```

Then:

1. update `pyproject.toml` version
2. commit the release change
3. push `main`
4. create and push tag `vX.Y.Z`

The release workflow should:

- verify tag/version match
- run release checks
- run async Postgres E2E
- build artifacts
- publish to PyPI
- create the GitHub release

If a release tag fails because of a real package bug, prefer fixing forward and
cutting the next version cleanly instead of hiding the failure.

## Agent Guidance

If you are an agent making changes here:

- prefer existing helpers and patterns over inventing new config surfaces
- preserve the distinction between:
  - store-only wrappers
  - persistence-bundle wrappers
  - graph wrappers
- do not make the API more nested when a top-level ergonomic helper is enough
- keep Postgres behavior compatible with real infra and CI
- test the exact make targets or public entrypoints you document
- if you add a shortcut like `make up`, use it yourself before claiming it works

## When In Doubt

Bias toward:

- pragmatic public API ergonomics
- real async Postgres compatibility
- deterministic E2E coverage
- documentation that matches what actually happens at the terminal
