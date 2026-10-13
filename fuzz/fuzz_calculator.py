"""Fuzz the deployed calculator; any attempt to call a device API is a failure."""

import importlib.util
import math
import struct
import sys
import types
from pathlib import Path

import atheris

ROOT = Path(__file__).resolve().parents[1]


def forbidden_device_call(*args, **kwargs):
    raise AssertionError("Calculator fuzzing must never call a device API")


# These imports are required by the single-file service, but the calculator
# below never uses them. They are deliberately fail-fast, not permissive mocks.
sys.modules["dbus"] = types.ModuleType("dbus")
vedbus = types.ModuleType("vedbus")
vedbus.VeDbusService = forbidden_device_call
sys.modules["vedbus"] = vedbus
shared = types.ModuleType("dbus_shared")
for name in ("PATH_DC_CURRENT", "PATH_DC_POWER", "PATH_DC_VOLTAGE"):
    setattr(shared, name, "/unused/" + name)
shared.POLL_INTERVAL_MS = 1000
for name in (
    "create_poll_function",
    "get_bus",
    "register_signal_handlers",
    "run_main_loop",
    "setup_dbus_paths_common",
    "setup_dbus_paths_dc",
    "setup_main_loop",
):
    setattr(shared, name, forbidden_device_call)
sys.modules["dbus_shared"] = shared

with atheris.instrument_imports():
    spec = importlib.util.spec_from_file_location(
        "fuzz_virtual_battery", ROOT / "dbus-virtual-battery.py"
    )
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)


def fuzz_one_input(data: bytes) -> None:
    if len(data) < 48:
        return
    voltage, current, chain_voltage, chain_current, soc, capacity = struct.unpack(
        "<6d", data[:48]
    )
    result = runtime.calculate_virtual_battery(
        voltage,
        current,
        [{"voltage": chain_voltage, "current": chain_current, "soc": soc}],
        capacity,
    )
    for key in (
        "voltage",
        "current",
        "power",
        "soc",
        "cell_voltage",
        "consumed_ah",
        "remaining_capacity",
        "time_to_go",
    ):
        value = result[key]
        assert value is None or math.isfinite(value), key  # nosec B101 - intentional test oracle
    if result["soc"] is not None:
        assert 0 <= result["soc"] <= 100  # nosec B101 - intentional test oracle
    if result["time_to_go"] is not None:
        assert 0 <= result["time_to_go"] <= runtime.TIME_TO_GO_CAP_SECONDS  # nosec B101 - intentional test oracle


if __name__ == "__main__":
    atheris.Setup(sys.argv, atheris.instrument_func(fuzz_one_input))
    atheris.Fuzz()
