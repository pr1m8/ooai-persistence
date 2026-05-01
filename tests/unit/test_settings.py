"""Unit tests for settings."""

from pathlib import Path

from ooai_persistence.settings import AppSettings, CheckpointerSettings


def test_default_infra_uris() -> None:
    settings = AppSettings.model_validate({})
    assert settings.infra.postgres_uri.startswith("postgresql://")
    assert settings.infra.redis_url.startswith("redis://")
    assert settings.infra.mongodb_uri.startswith("mongodb://")


def test_default_backends_are_auto() -> None:
    settings = AppSettings.model_validate({})
    assert settings.checkpointer.backend == "auto"
    assert settings.store.backend == "auto"
    assert settings.runtime.prefer_async is True


def test_resource_prefer_async_default_delegates_to_runtime() -> None:
    assert CheckpointerSettings().prefer_async is None


def test_memory_settings_disable_external_infra() -> None:
    settings = AppSettings.memory()
    assert settings.checkpointer.backend == "memory"
    assert settings.store.backend == "memory"
    assert settings.graph_cache.backend == "memory"
    assert settings.infra.postgres_enabled is False


def test_local_sqlite_settings_pin_paths() -> None:
    settings = AppSettings.local_sqlite("state.sqlite3")
    assert settings.checkpointer.backend == "sqlite"
    assert settings.checkpointer.sqlite_path == Path("state.sqlite3")
    assert settings.store.sqlite_path == Path("state.sqlite3")


def test_langsmith_settings_read_standard_env(monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_PROJECT", "persistence-tests")

    settings = AppSettings()

    assert settings.langsmith.tracing is True
    assert settings.langsmith.project == "persistence-tests"
