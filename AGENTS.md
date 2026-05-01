# AGENTS.md

## Purpose
This repository provides reusable persistence primitives for OOAI applications.
It owns persistence settings, serializer hardening, checkpointer/store/cache
resource creation, and sync/async persistence contexts.

## Boundaries
- Keep model/provider selection in `ooai-llm`.
- Keep runtime/session composition in `ooai-runtime`.
- Keep persistence-specific hardening and infra here.

## Coding guidelines
- Keep imports lazy for optional backends.
- Prefer typed settings over loose dictionaries.
- Treat strict serializer configuration as a first-class concern.
- Preserve clear separation between store, checkpointer, and graph cache.

## Tooling
- Use PDM as the package manager for this repository.
- Run `pdm install -G :all` before testing when dependencies may be missing.
- Use `pdm lock` or `pdm update` when dependency constraints or lockfile state need to change.
- Prefer `pdm run ...` for project commands so tests, linting, typing, examples,
  and docs run in the managed environment.

## Testing expectations
- Unit tests should cover pure logic and settings resolution.
- Integration tests should cover sync/async memory flows.
- E2E tests should exercise realistic package usage at the public API level.
