"""End-to-end tests for the packaged CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ooai_persistence.cli", *args],
        check=True,
        text=True,
        capture_output=True,
    )


def test_cli_doctor_json_reports_memory_resolution() -> None:
    result = _run_cli("doctor", "--backend", "memory", "--json")
    payload = json.loads(result.stdout)

    assert payload["package"] == "ooai-persistence"
    assert payload["resolution"]["checkpointer_sync"] == "memory"
    assert payload["optional_modules"]["langgraph"] is True


def test_cli_doctor_json_reports_postgres_async_resolution() -> None:
    result = _run_cli("doctor", "--backend", "postgres", "--json")
    payload = json.loads(result.stdout)

    assert payload["resolution"]["checkpointer_async"] == "postgres_async"
    assert payload["resolution"]["store_async"] == "postgres_async"
    assert payload["resolution"]["graph_cache"] == "memory"


def test_cli_smoke_memory_json() -> None:
    result = _run_cli("smoke", "--backend", "memory", "--json")
    payload = json.loads(result.stdout)

    assert payload == {
        "checkpointer": "ok",
        "graph_cache": "ok",
        "mode": "sync",
        "store": "ok",
    }


def test_cli_smoke_async_sqlite_json(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "cli.sqlite3"
    result = _run_cli(
        "smoke",
        "--backend",
        "sqlite",
        "--sqlite-path",
        str(sqlite_path),
        "--async",
        "--json",
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "async"
    assert payload["checkpointer"] == "ok"
    assert payload["store"] == "ok"
    assert payload["graph_cache"] == "ok"


def test_cli_env_writes_template(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    result = _run_cli("env", "--output", str(env_path))

    assert "wrote" in result.stdout
    assert "OOAI_PERSISTENCE_CHECKPOINTER__BACKEND=auto" in env_path.read_text()
