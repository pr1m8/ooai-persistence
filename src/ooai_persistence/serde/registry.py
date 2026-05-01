"""Msgpack allowlist registry helpers.

Purpose:
    Provide a reusable registry for custom types that should be allowed during
    strict LangGraph msgpack deserialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any


@dataclass(slots=True)
class MsgpackAllowlistRegistry:
    """Registry of ``(module, class_name)`` pairs for strict msgpack."""

    entries: set[tuple[str, str]] = field(default_factory=set)

    def register(self, module: str, name: str) -> None:
        """Register a symbol explicitly."""
        self.entries.add((module, name))

    def register_symbol(self, module: str, name: str) -> None:
        """Register a symbol explicitly.

        This is an ergonomic alias for :meth:`register`.
        """
        self.register(module, name)

    def register_type(self, type_: type[Any]) -> None:
        """Register a Python type using its module and class name."""
        self.register(type_.__module__, type_.__name__)

    def register_types(self, *types_: type[Any]) -> None:
        """Register multiple Python types."""
        for type_ in types_:
            self.register_type(type_)

    def register_import_string(self, import_string: str) -> None:
        """Register a type from ``module:ClassName`` or ``module.ClassName``.

        Args:
            import_string: Import path for the target class.

        Raises:
            ValueError: If the import string format is unsupported.
            AttributeError: If the target attribute does not exist.
            ModuleNotFoundError: If the target module cannot be imported.
        """
        if ":" in import_string:
            module_name, class_name = import_string.split(":", 1)
        else:
            module_name, _, class_name = import_string.rpartition(".")
            if not module_name:
                raise ValueError(
                    "Import string must look like 'package.module:ClassName' or "
                    "'package.module.ClassName'."
                )
        module = import_module(module_name)
        type_ = getattr(module, class_name)
        self.register_type(type_)

    def extend(self, entries: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> None:
        """Register multiple entries."""
        self.entries.update(entries)

    def as_tuple(self) -> tuple[tuple[str, str], ...]:
        """Return a stable sorted tuple of entries."""
        return tuple(sorted(self.entries))
