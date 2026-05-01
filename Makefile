SHELL := /bin/bash
COMPOSE := docker compose --env-file .env -f infra/compose.yaml

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: bootstrap install sync lock update format lint typecheck docs check test test-unit test-integration test-e2e test-cov smoke smoke-sqlite smoke-postgres-async clean env infra-up infra-ensure-postgres infra-up-redis infra-up-mongodb infra-test-postgres infra-down infra-reset infra-logs infra-psql infra-redis infra-mongo example-sync example-async

.env:
	cp .env.example .env

env: .env

bootstrap: env
	pdm install -G:all

install:
	pdm install -G:all

sync:
	pdm sync -G:all

lock:
	pdm lock

update:
	pdm update

format:
	pdm run ruff format src tests examples

lint:
	pdm run ruff check src tests examples

typecheck:
	pdm run pyright

docs:
	LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 pdm run sphinx-build -W -b html docs docs/_build/html

check: format lint typecheck test docs

test:
	pdm run pytest

test-unit:
	pdm run pytest tests/unit

test-integration:
	pdm run pytest -m integration tests/integration

test-e2e:
	pdm run pytest -m e2e tests/e2e

test-cov:
	pdm run pytest --cov=src/ooai_persistence --cov-report=term-missing --cov-report=xml --cov-report=html

smoke:
	pdm run ooai-persistence smoke --backend memory

smoke-sqlite:
	pdm run ooai-persistence smoke --backend sqlite

smoke-postgres-async:
	pdm run ooai-persistence smoke --backend postgres --async

infra-up: env
	@if command -v docker >/dev/null 2>&1; then \
		$(COMPOSE) up -d postgres; \
	else \
		echo "docker not found; using configured Postgres at $${OOAI_PERSISTENCE_INFRA__POSTGRES_HOST}:$${OOAI_PERSISTENCE_INFRA__POSTGRES_PORT}"; \
		$(MAKE) infra-ensure-postgres; \
	fi

infra-ensure-postgres: env
	pdm run ooai-persistence ensure-postgres

infra-up-redis: env
	$(COMPOSE) --profile redis up -d postgres redis

infra-up-mongodb: env
	$(COMPOSE) --profile mongodb up -d postgres mongodb

infra-test-postgres: infra-up
	$(MAKE) infra-ensure-postgres
	OOAI_PERSISTENCE_E2E_POSTGRES=1 pdm run pytest --no-cov tests/e2e/test_postgres_bundle.py
	OOAI_PERSISTENCE_E2E_POSTGRES=1 pdm run ooai-persistence smoke --backend postgres --async

infra-down: env
	$(COMPOSE) down

infra-reset: env
	$(COMPOSE) down -v --remove-orphans

infra-logs: env
	$(COMPOSE) logs -f

infra-psql: env
	$(COMPOSE) exec postgres psql -U "$${OOAI_PERSISTENCE_INFRA__POSTGRES_USER}" -d "$${OOAI_PERSISTENCE_INFRA__POSTGRES_DATABASE}"

infra-redis: env
	$(COMPOSE) exec redis redis-cli

infra-mongo: env
	$(COMPOSE) exec mongodb mongosh

example-sync:
	pdm run python examples/basic_sync.py

example-async:
	pdm run python examples/basic_async.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov coverage.xml
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
