"""Bootstrap helpers for persistence resources."""

from __future__ import annotations

from typing import Any

from ooai_persistence.registry import effective_setup_enabled
from ooai_persistence.settings import AppSettings, ResourceBackendSettings


async def maybe_async_setup(resource: Any, *, enabled: bool) -> None:
    """Run ``setup`` on an async resource when available and enabled."""
    if not enabled or resource is None:
        return
    setup = getattr(resource, "setup", None)
    if setup is None:
        return
    result = setup()
    if result is not None:
        await result


def maybe_setup(resource: Any, *, enabled: bool) -> None:
    """Run ``setup`` on a sync resource when available and enabled."""
    if not enabled or resource is None:
        return
    setup = getattr(resource, "setup", None)
    if setup is None:
        return
    setup()


def should_setup_for_resource(settings: AppSettings, resource: ResourceBackendSettings) -> bool:
    """Return whether a specific resource should run setup automatically."""
    return effective_setup_enabled(settings, resource)
