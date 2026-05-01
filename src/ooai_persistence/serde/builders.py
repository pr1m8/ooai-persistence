"""Serializer builders for ``ooai_persistence``.

Purpose:
    Build ``JsonPlusSerializer`` instances with strict msgpack-friendly
    allowlist configuration.
"""

from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from ooai_persistence.serde.registry import MsgpackAllowlistRegistry
from ooai_persistence.settings import AppSettings


def build_checkpointer_serde(
    settings: AppSettings,
    *,
    registry: MsgpackAllowlistRegistry | None = None,
    extra_allowlist: tuple[tuple[str, str], ...] | None = None,
) -> JsonPlusSerializer:
    """Build the configured serializer for checkpointers.

    Args:
        settings: Package settings.
        registry: Optional registry of known-safe persisted types.
        extra_allowlist: Optional additional allowlist entries.

    Returns:
        Configured serializer instance.
    """
    serializer = JsonPlusSerializer(
        allowed_msgpack_modules=() if settings.serializer.strict_msgpack else None,
    )

    merged: list[tuple[str, str]] = []
    if registry is not None:
        merged.extend(registry.as_tuple())
    merged.extend(settings.serializer.extra_allowlist)
    merged.extend(settings.checkpointer.serde_extra_allowlist)
    if extra_allowlist is not None:
        merged.extend(extra_allowlist)

    if merged:
        serializer = serializer.with_msgpack_allowlist(tuple(sorted(set(merged))))
    return serializer
