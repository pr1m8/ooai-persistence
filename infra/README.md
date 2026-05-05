# Local Infrastructure

The Docker Compose stack provides local services for integration and E2E
testing. The defaults are copied from `.env.example` by `make env`.

## Postgres

```bash
make bootstrap
make infra-up
make infra-up-docker
make test-e2e-postgres
make infra-psql
make infra-test-postgres
make infra-down
```

`make infra-up` is the default local-developer path. It uses the Postgres
server configured in `.env` and ensures the target database exists.

If you want the Compose-backed service explicitly, use:

```bash
make infra-up-docker
```

`make test-e2e-postgres` is the ergonomic Postgres path. It sets
`OOAI_PERSISTENCE_E2E_POSTGRES=1`, ensures the configured database exists, runs
the real public wrapper E2E tests, and then runs:

```bash
ooai-persistence smoke --backend postgres --async
```

`make infra-test-postgres` remains as a compatibility alias for the same flow.

When you are using a local or external Postgres server, `make infra-up` runs:

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
