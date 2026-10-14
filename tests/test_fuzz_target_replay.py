"""Replay the exact RC harness in isolation, including its device-call guard."""

# Runs only the fixed interpreter and repository-owned replay below, without a shell.
import subprocess  # nosec B404
import sys
from pathlib import Path


def test_committed_corpus_and_numeric_boundaries_use_the_real_harness():
    root = Path(__file__).resolve().parents[1]
    replay = r"""
import contextlib
import runpy
import struct
import sys
import types
from pathlib import Path

atheris = types.ModuleType("atheris")
atheris.instrument_imports = contextlib.nullcontext
sys.modules["atheris"] = atheris
harness = runpy.run_path("fuzz/fuzz_calculator.py")
assert Path(harness["runtime"].__file__).resolve() == Path("dbus-virtual-battery.py").resolve()
inputs = [seed.read_bytes() for seed in Path("fuzz/corpus/calculator").iterdir()]
assert inputs
inputs += [b"", b"short", bytes(48), b"\xff" * 48]
for capacity in (0.0, -1.0, 280.0, 1e308, float("inf"), float("nan")):
    inputs.append(struct.pack("<6d", 52.0, 10.0, 52.0, 9.0, 50.0, capacity))
for payload in inputs:
    harness["fuzz_one_input"](payload)
for call in (harness["vedbus"].VeDbusService, harness["shared"].get_bus):
    try:
        call()
    except AssertionError as error:
        assert "must never call a device API" in str(error)
    else:
        raise AssertionError("A device API guard became permissive")
"""
    subprocess.run([sys.executable, "-c", replay], cwd=root, check=True)  # nosec B603
