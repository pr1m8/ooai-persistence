# Local Infrastructure

The Docker Compose stack provides local services for integration and E2E
testing. The defaults are copied from `.env.example` by `make env`.

## Postgres

```bash
make bootstrap
make infra-up
make infra-psql
make infra-test-postgres
make infra-down
```

`make infra-test-postgres` sets `OOAI_PERSISTENCE_E2E_POSTGRES=1` and runs the
real async Postgres checkpointer/store E2E tests plus:

```bash
ooai-persistence smoke --backend postgres --async
```

When Docker is not installed, `make infra-up` falls back to the Postgres server
configured in `.env` and runs:

```bash
ooai-persistence ensure-postgres
```

That helper creates the configured database when the server is reachable but the
database is missing.

The Postgres connection is configured with:

- `OOAI_PERSISTENCE_INFRA__POSTGRES_HOST`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_PORT`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_DATABASE`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_USER`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_PASSWORD`
- `OOAI_PERSISTENCE_INFRA__POSTGRES_SSLMODE`

## Optional Services

Redis and MongoDB are opt-in Compose profiles:

```bash
make infra-up-redis
make infra-up-mongodb
```

Use `make infra-reset` to remove containers and named volumes.
