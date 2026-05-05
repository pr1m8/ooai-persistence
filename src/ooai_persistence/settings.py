"""Settings models for ``ooai_persistence``.

Purpose:
    Centralize configuration for LangGraph checkpointers, stores, serializer
    strictness, cache backends, and local infrastructure defaults.

Design:
    ``AppSettings`` is the package-local environment-backed settings entry
    point. It intentionally focuses on persistence concerns only so that
    upstream runtime/model packages can compose it cleanly.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, BaseModel, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ooai_persistence.types import GraphCacheBackend, PersistenceBackend


class RuntimeDefaultsSettings(BaseModel):
    """General runtime defaults for persistence resources."""

    setup_on_start: bool = True
    strict_msgpack: bool = True
    prefer_async: bool = True


class ResourceBackendSettings(BaseModel):
    """Shared backend settings for checkpointers and stores.

    Args:
        backend: Backend selection. ``"auto"`` prefers async Postgres, then
            async SQLite, then async MongoDB, then async Redis, and finally
            memory when no persistent backend is configured.
        prefer_async: Optional per-resource override for async backend
            preference.
        setup_on_start: Optional per-resource override for setup.
        sqlite_path: Path for SQLite-backed persistence, or ``None`` to
            disable SQLite as an ``"auto"`` fallback.
        postgres_uri: Optional PostgreSQL connection URI.
        redis_url: Optional Redis URL.
        mongodb_uri: Optional MongoDB connection URI.
        serde_extra_allowlist: Additional serializer allowlist entries.
    """

    backend: PersistenceBackend = "auto"
    prefer_async: bool | None = None
    setup_on_start: bool | None = None
    sqlite_path: Path | None = Path(".ooai/persistence/persistence.sqlite3")
    postgres_uri: str | None = None
    redis_url: str | None = None
    mongodb_uri: str | None = None
    serde_extra_allowlist: list[tuple[str, str]] = Field(default_factory=list)


class CheckpointerSettings(ResourceBackendSettings):
    """Checkpointer backend configuration."""


class StoreSettings(ResourceBackendSettings):
    """Long-term store backend configuration."""


class GraphCacheSettings(BaseModel):
    """Graph cache configuration."""

    enabled: bool = False
    backend: GraphCacheBackend = "none"
    sqlite_path: Path = Path(".ooai/cache/graph_cache.sqlite3")
    default_ttl_seconds: int | None = None


class SerializerSettings(BaseModel):
    """Serializer hardening settings."""

    strict_msgpack: bool = True
    auto_allowlist: bool = True
    extra_allowlist: list[tuple[str, str]] = Field(default_factory=list)


class InfraSettings(BaseModel):
    """Local infrastructure defaults for Docker Compose and development."""

    postgres_enabled: bool = True
    postgres_host: str = "localhost"
    postgres_port: int = 5442
    postgres_database: str = "ooai_persistence"
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("postgres")
    postgres_sslmode: str = "disable"

    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    mongodb_enabled: bool = False
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "ooai_persistence"
    mongodb_user: str | None = None
    mongodb_password: SecretStr | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def postgres_uri(self) -> str:
        """Return a standard PostgreSQL connection URI."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql://{self.postgres_user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            f"?sslmode={self.postgres_sslmode}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """Return a Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mongodb_uri(self) -> str:
        """Return a MongoDB URL."""
        auth = ""
        if self.mongodb_user and self.mongodb_password is not None:
            auth = f"{self.mongodb_user}:{self.mongodb_password.get_secret_value()}@"
        return f"mongodb://{auth}{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"


class LangSmithSettings(BaseSettings):
    """Tracing-related environment settings that persistence packages often need nearby."""

    model_config = SettingsConfigDict(
        env_prefix="LANGSMITH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tracing: bool = Field(
        default=False,
        validation_alias=AliasChoices("LANGSMITH_TRACING", "TRACING"),
    )
    api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "API_KEY"),
    )
    project: str = Field(
        default="ooai",
        validation_alias=AliasChoices("LANGSMITH_PROJECT", "PROJECT"),
    )
    endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_ENDPOINT", "ENDPOINT"),
    )


class AppSettings(BaseSettings):
    """Top-level settings for ``ooai_persistence``.

    Examples:
        >>> settings = AppSettings()
        >>> settings.checkpointer.backend in {
        ...     "auto", "memory", "postgres", "redis", "sqlite",
        ...     "sqlite_async", "postgres_async", "none", "mongodb",
        ...     "mongodb_async", "redis_async",
        ... }
        True
    """

    model_config = SettingsConfigDict(
        env_prefix="OOAI_PERSISTENCE_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    runtime: RuntimeDefaultsSettings = Field(default_factory=RuntimeDefaultsSettings)
    checkpointer: CheckpointerSettings = Field(default_factory=CheckpointerSettings)
    store: StoreSettings = Field(default_factory=StoreSettings)
    graph_cache: GraphCacheSettings = Field(default_factory=GraphCacheSettings)
    serializer: SerializerSettings = Field(default_factory=SerializerSettings)
    infra: InfraSettings = Field(default_factory=InfraSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)

    @classmethod
    def memory(cls, *, graph_cache: bool = True) -> AppSettings:
        """Return settings for a zero-infrastructure in-memory persistence bundle."""
        return cls.model_validate(
            {
                "infra": {
                    "postgres_enabled": False,
                    "redis_enabled": False,
                    "mongodb_enabled": False,
                },
                "checkpointer": {"backend": "memory"},
                "store": {"backend": "memory"},
                "graph_cache": {
                    "enabled": graph_cache,
                    "backend": "memory" if graph_cache else "none",
                },
            }
        )

    @classmethod
    def local_sqlite(
        cls, path: str | Path = ".ooai/persistence/persistence.sqlite3"
    ) -> AppSettings:
        """Return settings for local SQLite-backed development persistence."""
        sqlite_path = Path(path)
        return cls.model_validate(
            {
                "infra": {
                    "postgres_enabled": False,
                    "redis_enabled": False,
                    "mongodb_enabled": False,
                },
                "checkpointer": {"backend": "sqlite", "sqlite_path": sqlite_path},
                "store": {"backend": "sqlite", "sqlite_path": sqlite_path},
            }
        )

    @classmethod
    def postgres(
        cls,
        uri: str | None = None,
        *,
        host: str = "localhost",
        port: int = 5442,
        database: str = "ooai_persistence",
        user: str = "postgres",
        password: str = "postgres",
        sslmode: str = "disable",
        graph_cache: bool = True,
    ) -> AppSettings:
        """Return settings for async Postgres-backed persistence.

        Pass either a full ``uri`` or individual connection parts.
        """
        if uri is not None:
            payload = {
                "checkpointer": {"backend": "postgres_async", "postgres_uri": uri},
                "store": {"backend": "postgres_async", "postgres_uri": uri},
                "graph_cache": {
                    "enabled": graph_cache,
                    "backend": "memory" if graph_cache else "none",
                },
            }
            return cls.model_validate(payload)

        payload = {
            "infra": {
                "postgres_enabled": True,
                "postgres_host": host,
                "postgres_port": port,
                "postgres_database": database,
                "postgres_user": user,
                "postgres_password": password,
                "postgres_sslmode": sslmode,
                "redis_enabled": False,
                "mongodb_enabled": False,
            },
            "checkpointer": {"backend": "postgres_async"},
            "store": {"backend": "postgres_async"},
            "graph_cache": {
                "enabled": graph_cache,
                "backend": "memory" if graph_cache else "none",
            },
        }
        return cls.model_validate(payload)


def memory_settings(*, graph_cache: bool = True) -> AppSettings:
    """Return a zero-infrastructure in-memory settings preset."""
    return AppSettings.memory(graph_cache=graph_cache)


def sqlite_settings(
    path: str | Path = ".ooai/persistence/persistence.sqlite3",
) -> AppSettings:
    """Return a local SQLite settings preset."""
    return AppSettings.local_sqlite(path)


def postgres_settings(
    uri: str | None = None,
    *,
    host: str = "localhost",
    port: int = 5442,
    database: str = "ooai_persistence",
    user: str = "postgres",
    password: str = "postgres",
    sslmode: str = "disable",
    graph_cache: bool = True,
) -> AppSettings:
    """Return an async Postgres settings preset."""
    return AppSettings.postgres(
        uri,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode=sslmode,
        graph_cache=graph_cache,
    )
