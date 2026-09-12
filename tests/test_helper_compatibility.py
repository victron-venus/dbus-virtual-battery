"""Validate both deployed helper layouts without running a D-Bus service."""

import builtins
import runpy
import sys
from pathlib import Path

import pytest

from tests.fake_dbus import driver_modules


def test_existing_mqtt_helper_supports_standalone_runtime(monkeypatch):
    modules = driver_modules()
    helper = modules.pop("dbus_shared")
    modules["dbus_shared"] = None
    modules["dbus_mqtt_battery"] = helper
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    root = Path(__file__).resolve().parents[1]
    runtime = runpy.run_path(
        str(root / "dbus-virtual-battery.py"), run_name="helper_smoke"
    )
    assert runtime["get_bus"] is helper.get_bus
    assert runtime["VERSION"] == (root / "version").read_text().strip().removeprefix(
        "v"
    )
    assert runtime["VERSION"] != helper.VERSION
    helper.get_bus.assert_not_called()


def test_broken_installed_helper_is_not_silently_replaced(monkeypatch):
    original = builtins.__import__

    def fail_dependency(name, *args, **kwargs):
        if name == "dbus_shared":
            raise ModuleNotFoundError(
                "Missing internal dependency", name="helper_dependency"
            )
        return original(name, *args, **kwargs)

    modules = driver_modules()
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(builtins, "__import__", fail_dependency)
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ModuleNotFoundError, match="Missing internal dependency"):
        runpy.run_path(str(root / "dbus-virtual-battery.py"), run_name="helper_smoke")
