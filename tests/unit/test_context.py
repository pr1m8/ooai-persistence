"""Unit tests for context helper defaults."""

from ooai_persistence.context import _postgres_open_settings


def test_postgres_open_settings_reads_env_defaults(monkeypatch) -> None:
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_HOST", "db.example")
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_PORT", "5432")
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_DATABASE", "appdb")
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_USER", "app")
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_SSLMODE", "require")

    settings = _postgres_open_settings(
        None,
        host=None,
        port=None,
        database=None,
        user=None,
        password=None,
        sslmode=None,
        graph_cache=True,
    )

    assert settings.infra.postgres_host == "db.example"
    assert settings.infra.postgres_port == 5432
    assert settings.infra.postgres_database == "appdb"
    assert settings.infra.postgres_user == "app"
    assert settings.infra.postgres_password.get_secret_value() == "secret"
    assert settings.infra.postgres_sslmode == "require"


def test_postgres_open_settings_explicit_values_override_env(monkeypatch) -> None:
    monkeypatch.setenv("OOAI_PERSISTENCE_INFRA__POSTGRES_PORT", "5432")

    settings = _postgres_open_settings(
        None,
        host="localhost",
        port=5442,
        database="override",
        user="postgres",
        password="postgres",
        sslmode="disable",
        graph_cache=False,
    )

    assert settings.infra.postgres_port == 5442
    assert settings.infra.postgres_database == "override"
    assert settings.graph_cache.enabled is False
    assert settings.graph_cache.backend == "none"
