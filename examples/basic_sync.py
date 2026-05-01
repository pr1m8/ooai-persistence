"""Basic sync example for ``ooai_persistence``."""

from __future__ import annotations

from ooai_persistence.context import persistence_context
from ooai_persistence.settings import AppSettings


def main() -> None:
    """Open the configured persistence bundle and print active resources."""
    settings = AppSettings()
    with persistence_context(settings) as bundle:
        print(bundle.checkpointer)
        print(bundle.store)
        print(bundle.graph_cache)


if __name__ == "__main__":
    main()
