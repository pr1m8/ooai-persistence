"""Shared types for ``ooai_persistence``."""

from __future__ import annotations

from typing import Literal

type PersistenceBackend = Literal[
    "auto",
    "none",
    "memory",
    "sqlite",
    "sqlite_async",
    "postgres",
    "postgres_async",
    "redis",
    "redis_async",
    "mongodb",
    "mongodb_async",
]

type GraphCacheBackend = Literal["none", "memory", "sqlite"]
