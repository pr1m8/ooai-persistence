"""Unit tests for the ooai-persistence CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ooai_persistence import cli


def test_cli_doctor_json_outputs_resolution(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["doctor", "--backend", "postgres", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["resolution"]["checkpointer_async"] == "postgres_async"
    assert payload["resolution"]["store_async"] == "postgres_async"


def test_cli_doctor_text_outputs_sections(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["doctor", "--backend", "memory"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "resolution:" in output
    assert "optional_modules:" in output


def test_cli_smoke_memory_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["smoke", "--backend", "memory", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["checkpointer"] == "ok"
    assert payload["store"] == "ok"
    assert payload["graph_cache"] == "ok"


def test_cli_smoke_async_memory_text(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["smoke", "--backend", "memory", "--async"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "mode: async" in output
    assert "store: ok" in output


def test_cli_smoke_sqlite_without_cache(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = cli.main(
        [
            "smoke",
            "--backend",
            "sqlite",
            "--sqlite-path",
            str(tmp_path / "state.sqlite3"),
            "--no-cache",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["graph_cache"] == "skipped"


def test_cli_smoke_json_reports_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_smoke(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "run_sync_smoke", fail_smoke)

    exit_code = cli.main(["smoke", "--backend", "memory", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload == {"error": "database unavailable", "ok": False}


def test_cli_env_prints_template(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["env"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "OOAI_PERSISTENCE_CHECKPOINTER__BACKEND=auto" in output


def test_cli_env_writes_template(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env_path = tmp_path / ".env"

    exit_code = cli.main(["env", "--output", str(env_path)])

    assert exit_code == 0
    assert "wrote" in capsys.readouterr().out
    assert "OOAI_PERSISTENCE_STORE__BACKEND=auto" in env_path.read_text()


def test_cli_env_refuses_existing_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("already here", encoding="utf-8")

    exit_code = cli.main(["env", "--output", str(env_path)])

    assert exit_code == 2
    assert "already exists" in capsys.readouterr().err


def test_cli_env_force_overwrites_existing_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("already here", encoding="utf-8")

    exit_code = cli.main(["env", "--output", str(env_path), "--force"])

    assert exit_code == 0
    assert "OOAI_PERSISTENCE_RUNTIME__SETUP_ON_START=true" in env_path.read_text()


def test_cli_ensure_postgres_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "_ensure_postgres_database",
        lambda _settings: {"database": "ooai_persistence", "created": False, "ok": True},
    )

    exit_code = cli.main(["ensure-postgres", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload == {"created": False, "database": "ooai_persistence", "ok": True}


def test_cli_ensure_postgres_reports_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(_settings: object) -> object:
        raise RuntimeError("postgres unavailable")

    monkeypatch.setattr(cli, "_ensure_postgres_database", fail)

    exit_code = cli.main(["ensure-postgres", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload == {"error": "postgres unavailable", "ok": False}
