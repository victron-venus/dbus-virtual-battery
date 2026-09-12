"""Import the actual entrypoint with isolated hardware driver doubles."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

from tests.fake_dbus import driver_modules


def load_runtime():
    """Execute production definitions without invoking main or hardware imports."""
    path = Path(__file__).resolve().parents[1] / "dbus-virtual-battery.py"
    spec = importlib.util.spec_from_file_location("virtual_battery_runtime", path)
    module = importlib.util.module_from_spec(spec)
    original_path = sys.path[:]
    try:
        with patch.dict(sys.modules, driver_modules()):
            spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_path
    return module


runtime = load_runtime()
