from __future__ import annotations

import sys
import types

from ooai_persistence.serde.registry import MsgpackAllowlistRegistry


class ExampleType:
    pass


def test_registry_register_type() -> None:
    registry = MsgpackAllowlistRegistry()
    registry.register_type(ExampleType)
    assert (ExampleType.__module__, ExampleType.__name__) in registry.as_tuple()


def test_registry_register_import_string_module_colon_name() -> None:
    module = types.ModuleType("tests.fake_models")

    class FakeModel:
        pass

    FakeModel.__module__ = module.__name__
    module.__dict__["FakeModel"] = FakeModel
    sys.modules[module.__name__] = module

    registry = MsgpackAllowlistRegistry()
    registry.register_import_string("tests.fake_models:FakeModel")

    assert (module.__name__, "FakeModel") in registry.as_tuple()


def test_registry_register_import_string_module_dot_name() -> None:
    module = types.ModuleType("tests.fake_dot_models")

    class DotModel:
        pass

    DotModel.__module__ = module.__name__
    module.__dict__["DotModel"] = DotModel
    sys.modules[module.__name__] = module

    registry = MsgpackAllowlistRegistry()
    registry.register_import_string("tests.fake_dot_models.DotModel")

    assert (module.__name__, "DotModel") in registry.as_tuple()


def test_registry_register_import_string_requires_module() -> None:
    registry = MsgpackAllowlistRegistry()
    try:
        registry.register_import_string("OnlyAClass")
    except ValueError as exc:
        assert "Import string must look like" in str(exc)
    else:
        raise AssertionError("Expected invalid import string to raise ValueError.")


def test_registry_extend_sorts_entries() -> None:
    registry = MsgpackAllowlistRegistry()
    registry.register_symbol("z_mod", "Zed")
    registry.extend([("a_mod", "Alpha")])
    assert registry.as_tuple() == (("a_mod", "Alpha"), ("z_mod", "Zed"))
