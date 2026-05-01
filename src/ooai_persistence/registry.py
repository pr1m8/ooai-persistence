"""Backend resolution helpers for ``ooai_persistence``."""

from __future__ import annotations

from ooai_persistence.settings import AppSettings, ResourceBackendSettings
from ooai_persistence.types import PersistenceBackend

SYNC_EQUIVALENTS: dict[PersistenceBackend, PersistenceBackend] = {
    "auto": "auto",
    "none": "none",
    "memory": "memory",
    "sqlite_async": "sqlite",
    "postgres_async": "postgres",
    "redis_async": "redis",
    "mongodb_async": "mongodb",
    "sqlite": "sqlite",
    "postgres": "postgres",
    "redis": "redis",
    "mongodb": "mongodb",
}

ASYNC_EQUIVALENTS: dict[PersistenceBackend, PersistenceBackend] = {
    "auto": "auto",
    "none": "none",
    "memory": "memory",
    "sqlite": "sqlite_async",
    "postgres": "postgres_async",
    "redis": "redis_async",
    "mongodb": "mongodb_async",
    "sqlite_async": "sqlite_async",
    "postgres_async": "postgres_async",
    "redis_async": "redis_async",
    "mongodb_async": "mongodb_async",
}


def effective_setup_enabled(settings: AppSettings, resource: ResourceBackendSettings) -> bool:
    """Return whether setup should run for a resource."""
    return (
        settings.runtime.setup_on_start
        if resource.setup_on_start is None
        else resource.setup_on_start
    )


def resolve_backend(
    resource: ResourceBackendSettings,
    settings: AppSettings,
    *,
    prefer_async: bool | None = None,
) -> PersistenceBackend:
    """Resolve an effective backend.

    Args:
        resource: Resource-specific settings.
        settings: Top-level app settings.
        prefer_async: Optional override for async preference.

    Returns:
        Effective backend string.
    """
    requested = resource.backend
    if requested != "auto":
        if prefer_async is None:
            return requested
        mapping = ASYNC_EQUIVALENTS if prefer_async else SYNC_EQUIVALENTS
        return mapping[requested]

    if prefer_async is None:
        use_async = (
            settings.runtime.prefer_async
            if resource.prefer_async is None
            else resource.prefer_async
        )
    else:
        use_async = prefer_async
    if resource.postgres_uri or settings.infra.postgres_enabled:
        return "postgres_async" if use_async else "postgres"
    if resource.sqlite_path:
        return "sqlite_async" if use_async else "sqlite"
    if resource.mongodb_uri or settings.infra.mongodb_enabled:
        return "mongodb_async" if use_async else "mongodb"
    if resource.redis_url or settings.infra.redis_enabled:
        return "redis_async" if use_async else "redis"
    return "memory"
