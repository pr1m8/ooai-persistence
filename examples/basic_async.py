"""Basic async example for ``ooai_persistence``."""

from __future__ import annotations

import asyncio

from ooai_persistence.context import async_persistence_context
from ooai_persistence.settings import AppSettings


async def main() -> None:
    """Open the configured persistence bundle and print active resources."""
    settings = AppSettings()
    async with async_persistence_context(settings) as bundle:
        print(bundle.checkpointer)
        print(bundle.store)
        print(bundle.graph_cache)


if __name__ == "__main__":
    asyncio.run(main())
