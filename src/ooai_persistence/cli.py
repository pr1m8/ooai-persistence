"""Command-line interface for ooai-persistence."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from ooai_persistence.registry import resolve_backend
from ooai_persistence.settings import AppSettings
from ooai_persistence.smoke import SmokeReport, run_async_smoke, run_sync_smoke

ENV_TEMPLATE = """\
OOAI_PERSISTENCE_RUNTIME__SETUP_ON_START=true
OOAI_PERSISTENCE_RUNTIME__STRICT_MSGPACK=true
OOAI_PERSISTENCE_RUNTIME__PREFER_ASYNC=true

OOAI_PERSISTENCE_CHECKPOINTER__BACKEND=auto
OOAI_PERSISTENCE_STORE__BACKEND=auto
OOAI_PERSISTENCE_GRAPH_CACHE__ENABLED=false
OOAI_PERSISTENCE_GRAPH_CACHE__BACKEND=none

OOAI_PERSISTENCE_INFRA__POSTGRES_ENABLED=true
OOAI_PERSISTENCE_INFRA__POSTGRES_HOST=localhost
OOAI_PERSISTENCE_INFRA__POSTGRES_PORT=5442
OOAI_PERSISTENCE_INFRA__POSTGRES_DATABASE=ooai_persistence
OOAI_PERSISTENCE_INFRA__POSTGRES_USER=postgres
OOAI_PERSISTENCE_INFRA__POSTGRES_PASSWORD=postgres
OOAI_PERSISTENCE_INFRA__POSTGRES_SSLMODE=disable

OOAI_PERSISTENCE_INFRA__REDIS_ENABLED=false
OOAI_PERSISTENCE_INFRA__REDIS_HOST=localhost
OOAI_PERSISTENCE_INFRA__REDIS_PORT=6379
OOAI_PERSISTENCE_INFRA__REDIS_DB=0

OOAI_PERSISTENCE_INFRA__MONGODB_ENABLED=false
OOAI_PERSISTENCE_INFRA__MONGODB_HOST=localhost
OOAI_PERSISTENCE_INFRA__MONGODB_PORT=27017
OOAI_PERSISTENCE_INFRA__MONGODB_DATABASE=ooai_persistence

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=ooai
LANGSMITH_ENDPOINT=
"""


def _package_version() -> str:
    try:
        return version("ooai-persistence")
    except PackageNotFoundError:
        return "editable"


def _settings_for_backend(args: argparse.Namespace) -> AppSettings:
    if args.backend == "memory":
        return AppSettings.memory(graph_cache=not args.no_cache)
    if args.backend == "sqlite":
        settings = AppSettings.local_sqlite(args.sqlite_path)
        settings.graph_cache.enabled = not args.no_cache
        settings.graph_cache.backend = "sqlite" if not args.no_cache else "none"
        settings.graph_cache.sqlite_path = Path(args.sqlite_path).with_name("graph-cache.sqlite3")
        return settings
    if args.backend == "postgres":
        settings = AppSettings()
        settings.checkpointer.backend = "postgres"
        settings.store.backend = "postgres"
        settings.graph_cache.enabled = not args.no_cache
        settings.graph_cache.backend = "memory" if not args.no_cache else "none"
        return settings
    return AppSettings()


def _resolution(settings: AppSettings) -> dict[str, str]:
    return {
        "checkpointer_sync": resolve_backend(settings.checkpointer, settings, prefer_async=False),
        "checkpointer_async": resolve_backend(settings.checkpointer, settings, prefer_async=True),
        "store_sync": resolve_backend(settings.store, settings, prefer_async=False),
        "store_async": resolve_backend(settings.store, settings, prefer_async=True),
        "graph_cache": settings.graph_cache.backend if settings.graph_cache.enabled else "none",
    }


def _doctor_payload(settings: AppSettings) -> dict[str, Any]:
    optional_modules = {
        "langgraph": "langgraph",
        "postgres": "langgraph.checkpoint.postgres",
        "sqlite": "langgraph.checkpoint.sqlite",
        "redis": "langgraph.checkpoint.redis",
        "mongodb_checkpointer": "langgraph.checkpoint.mongodb",
        "langsmith": "langsmith",
    }
    return {
        "package": "ooai-persistence",
        "version": _package_version(),
        "resolution": _resolution(settings),
        "langsmith": {
            "tracing": settings.langsmith.tracing,
            "project": settings.langsmith.project,
            "endpoint": settings.langsmith.endpoint,
            "api_key_configured": settings.langsmith.api_key is not None,
        },
        "optional_modules": {
            name: find_spec(module) is not None for name, module in optional_modules.items()
        },
    }


def _ensure_postgres_database(settings: AppSettings) -> dict[str, Any]:
    from psycopg import connect, sql

    infra = settings.infra
    password = infra.postgres_password.get_secret_value()
    admin_uri = (
        f"postgresql://{infra.postgres_user}:{password}@"
        f"{infra.postgres_host}:{infra.postgres_port}/postgres"
        f"?sslmode={infra.postgres_sslmode}"
    )
    target_uri = settings.checkpointer.postgres_uri or infra.postgres_uri

    with connect(admin_uri, autocommit=True) as conn:
        exists = conn.execute(
            "select 1 from pg_database where datname = %s",
            [infra.postgres_database],
        ).fetchone()
        created = exists is None
        if created:
            conn.execute(
                sql.SQL("create database {}").format(sql.Identifier(infra.postgres_database))
            )

    with connect(target_uri, autocommit=True) as conn:
        conn.execute("select 1").fetchone()

    return {
        "database": infra.postgres_database,
        "host": infra.postgres_host,
        "port": str(infra.postgres_port),
        "created": created,
        "ok": True,
    }


def _print_payload(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for child_key, child_value in value.items():
                print(f"  {child_key}: {child_value}")
        else:
            print(f"{key}: {value}")


def _print_smoke(report: SmokeReport, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
        return
    print(f"mode: {report.mode}")
    print(f"checkpointer: {report.checkpointer}")
    print(f"store: {report.store}")
    print(f"graph_cache: {report.graph_cache}")


def _cmd_doctor(args: argparse.Namespace) -> int:
    settings = _settings_for_backend(args)
    _print_payload(_doctor_payload(settings), json_output=args.json)
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    settings = _settings_for_backend(args)
    try:
        report = (
            asyncio.run(run_async_smoke(settings)) if args.async_mode else run_sync_smoke(settings)
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "ok": False}, indent=2, sort_keys=True))
        else:
            print(f"smoke failed: {exc}", file=sys.stderr)
        return 1
    _print_smoke(report, json_output=args.json)
    return 0 if report.ok else 1


def _cmd_env(args: argparse.Namespace) -> int:
    if args.output is None:
        print(ENV_TEMPLATE, end="")
        return 0
    path = Path(args.output)
    if path.exists() and not args.force:
        print(f"{path} already exists; pass --force to overwrite.", file=sys.stderr)
        return 2
    path.write_text(ENV_TEMPLATE, encoding="utf-8")
    print(f"wrote {path}")
    return 0


def _cmd_ensure_postgres(args: argparse.Namespace) -> int:
    try:
        payload = _ensure_postgres_database(AppSettings())
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "ok": False}, indent=2, sort_keys=True))
        else:
            print(f"postgres setup failed: {exc}", file=sys.stderr)
        return 1
    _print_payload(payload, json_output=args.json)
    return 0


def _add_backend_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=("auto", "memory", "sqlite", "postgres"),
        default="memory",
        help="Backend preset to inspect or smoke test.",
    )
    parser.add_argument(
        "--sqlite-path",
        default=".ooai/persistence/cli-smoke.sqlite3",
        help="SQLite path for --backend sqlite.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable graph cache for the selected preset.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="ooai-persistence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Inspect resolved settings and optional extras.")
    _add_backend_options(doctor)
    doctor.add_argument("--json", action="store_true", help="Emit JSON.")
    doctor.set_defaults(func=_cmd_doctor)

    smoke = subparsers.add_parser("smoke", help="Run a public API persistence smoke check.")
    _add_backend_options(smoke)
    smoke.add_argument(
        "--async", dest="async_mode", action="store_true", help="Use async resources."
    )
    smoke.add_argument("--json", action="store_true", help="Emit JSON.")
    smoke.set_defaults(func=_cmd_smoke)

    env = subparsers.add_parser("env", help="Print or write an example environment file.")
    env.add_argument("--output", "-o", help="Write the template to a path instead of stdout.")
    env.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    env.set_defaults(func=_cmd_env)

    ensure_postgres = subparsers.add_parser(
        "ensure-postgres",
        help="Create and verify the configured Postgres database.",
    )
    ensure_postgres.add_argument("--json", action="store_true", help="Emit JSON.")
    ensure_postgres.set_defaults(func=_cmd_ensure_postgres)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
