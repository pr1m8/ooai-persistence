"""Unit tests for backend resolution helpers."""

from ooai_persistence.registry import effective_setup_enabled, resolve_backend
from ooai_persistence.settings import AppSettings, ResourceBackendSettings


def test_resolve_backend_prefers_async_postgres_when_auto() -> None:
    settings = AppSettings()
    resource = ResourceBackendSettings(backend="auto")
    assert resolve_backend(resource, settings) == "postgres_async"


def test_resolve_backend_prefers_memory_when_infra_disabled_and_no_overrides() -> None:
    settings = AppSettings.model_validate(
        {
            "infra": {
                "postgres_enabled": False,
                "redis_enabled": False,
                "mongodb_enabled": False,
            }
        }
    )
    resource = ResourceBackendSettings(backend="auto", sqlite_path=None)
    assert resolve_backend(resource, settings) == "memory"


def test_resolve_backend_uses_runtime_async_preference() -> None:
    settings = AppSettings.model_validate({"runtime": {"prefer_async": False}})
    resource = ResourceBackendSettings(backend="auto")
    assert resolve_backend(resource, settings) == "postgres"


def test_resolve_backend_resource_prefer_async_overrides_runtime() -> None:
    settings = AppSettings.model_validate({"runtime": {"prefer_async": False}})
    resource = ResourceBackendSettings(backend="auto", prefer_async=True)
    assert resolve_backend(resource, settings) == "postgres_async"


def test_resolve_backend_maps_explicit_async_backend_to_sync() -> None:
    settings = AppSettings()
    resource = ResourceBackendSettings(backend="postgres_async")
    assert resolve_backend(resource, settings, prefer_async=False) == "postgres"


def test_effective_setup_enabled_uses_override() -> None:
    settings = AppSettings.model_validate({"runtime": {"setup_on_start": True}})
    resource = ResourceBackendSettings(setup_on_start=False)
    assert effective_setup_enabled(settings, resource) is False
