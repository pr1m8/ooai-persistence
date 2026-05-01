"""Unit tests for bootstrap helpers."""

from __future__ import annotations

from ooai_persistence.bootstrap import maybe_async_setup, maybe_setup


class Dummy:
    def __init__(self) -> None:
        self.called = False

    def setup(self) -> None:
        self.called = True


def test_maybe_setup_calls_setup_when_enabled() -> None:
    resource = Dummy()
    maybe_setup(resource, enabled=True)
    assert resource.called is True


def test_maybe_setup_skips_disabled_and_missing_resources() -> None:
    resource = Dummy()
    maybe_setup(resource, enabled=False)
    maybe_setup(None, enabled=True)
    maybe_setup(object(), enabled=True)
    assert resource.called is False


async def test_maybe_async_setup_awaits_result() -> None:
    class AsyncDummy:
        def __init__(self) -> None:
            self.called = False

        async def _setup(self) -> None:
            self.called = True

        def setup(self) -> object:
            return self._setup()

    resource = AsyncDummy()
    await maybe_async_setup(resource, enabled=True)
    assert resource.called is True


async def test_maybe_async_setup_handles_sync_setup() -> None:
    resource = Dummy()
    await maybe_async_setup(resource, enabled=True)
    assert resource.called is True
