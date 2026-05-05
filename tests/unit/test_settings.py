"""Unit tests for settings."""

from pathlib import Path

from ooai_persistence.settings import (
    AppSettings,
    CheckpointerSettings,
    memory_settings,
    postgres_settings,
    sqlite_settings,
)


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


def test_postgres_settings_use_async_postgres_backend() -> None:
    settings = AppSettings.postgres(database="demo")
    assert settings.checkpointer.backend == "postgres_async"
    assert settings.store.backend == "postgres_async"
    assert settings.infra.postgres_database == "demo"
    assert settings.graph_cache.backend == "memory"


def test_postgres_settings_accept_explicit_uri() -> None:
    settings = AppSettings.postgres("postgresql://user:pass@host:5432/app?sslmode=disable")
    assert settings.checkpointer.postgres_uri is not None
    assert settings.checkpointer.postgres_uri.startswith("postgresql://user:pass@host")
    assert settings.store.postgres_uri == settings.checkpointer.postgres_uri


def test_top_level_settings_helpers_delegate_to_appsettings() -> None:
    assert memory_settings().checkpointer.backend == "memory"
    assert sqlite_settings("demo.sqlite3").store.sqlite_path == Path("demo.sqlite3")
    assert postgres_settings(database="demo").store.backend == "postgres_async"


def test_langsmith_settings_read_standard_env(monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_PROJECT", "persistence-tests")

    settings = AppSettings()

    assert settings.langsmith.tracing is True
    assert settings.langsmith.project == "persistence-tests"


def test_standard_postgres_env_aliases_are_supported(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "db.example")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "appdb")
    monkeypatch.setenv("POSTGRES_USER", "app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_POOL_MIN_SIZE", "3")
    monkeypatch.setenv("POSTGRES_POOL_MAX_SIZE", "12")

    settings = AppSettings()

    assert settings.infra.postgres_host == "db.example"
    assert settings.infra.postgres_port == 5432
    assert settings.infra.postgres_database == "appdb"
    assert settings.infra.postgres_user == "app"
    assert settings.infra.postgres_password.get_secret_value() == "secret"
    assert settings.infra.postgres_sslmode == "require"
    assert settings.infra.postgres_pool_min_size == 3
    assert settings.infra.postgres_pool_max_size == 12


def test_database_url_and_supabase_db_url_map_to_postgres_uri(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example:5432/appdb?sslmode=require")

    settings = AppSettings()

    assert settings.checkpointer.postgres_uri == settings.store.postgres_uri
    assert settings.checkpointer.postgres_uri is not None
    assert "db.example:5432/appdb" in settings.checkpointer.postgres_uri

    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv(
        "SUPABASE_DB_URL",
        "postgresql://postgres:secret@aws-0-ca-central-1.pooler.supabase.com:6543/postgres",
    )

    supabase_settings = AppSettings()

    assert supabase_settings.checkpointer.postgres_uri == supabase_settings.store.postgres_uri
    assert supabase_settings.checkpointer.postgres_uri is not None
    assert "supabase.com:6543/postgres" in supabase_settings.checkpointer.postgres_uri
