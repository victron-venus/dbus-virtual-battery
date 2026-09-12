"""Check the actual release archive with explicitly mocked external prerequisites."""

import hashlib
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from scripts.build_release import build_archive

ROOT = Path(__file__).resolve().parents[1]
TAG = (ROOT / "version").read_text().strip()


def test_archive_contains_the_versioned_runtime(tmp_path):
    """Verify archived bytes, reproducibility, installer mode and extracted imports."""
    archive = build_archive(ROOT, TAG, tmp_path)
    assert (
        f'version = "{TAG.removeprefix("v")}"' in (ROOT / "pyproject.toml").read_text()
    )
    first_bytes = archive.read_bytes()
    checksum = archive.with_suffix(".gz.sha256").read_text().split()[0]
    assert hashlib.sha256(first_bytes).hexdigest() == checksum
    assert build_archive(ROOT, TAG, tmp_path).read_bytes() == first_bytes
    with tarfile.open(archive) as package:
        assert set(package.getnames()) == {
            f"dbus-virtual-battery/{name}"
            for name in ("dbus-virtual-battery.py", "setup", "gitHubInfo", "version")
        }
        assert package.getmember("dbus-virtual-battery/setup").mode == 0o755
        package.extractall(tmp_path / "extracted", filter="data")
    root = tmp_path / "extracted/dbus-virtual-battery"
    assert (root / "version").read_text().strip() == TAG
    subprocess.run(["bash", "-n", str(root / "setup")], check=True)
    # The separately installed dbus_shared and device drivers are explicit
    # prerequisites, mocked only at their boundary. The calculator and CLI
    # come from the downloaded-layout entrypoint, outside this checkout.
    smoke = """
import runpy
import sys
from unittest.mock import Mock
adapters = runpy.run_path(sys.argv[2])["driver_modules"]()
sys.modules.update(adapters)
entry = runpy.run_path(sys.argv[1] + "/dbus-virtual-battery.py", run_name="package_smoke")
assert entry["VERSION"] == sys.argv[3]
assert adapters["dbus_shared"].VERSION != entry["VERSION"]
state = entry["calculate_virtual_battery"](52, 20, [{"voltage": 52, "current": 5, "soc": 80}], 280)
assert state["current"] == 15 and state["power"] == 780
main = entry["main"]
factory = Mock()
main.__globals__["VirtualBatteryService"] = factory
main.__globals__["sleep"] = Mock()
sys.argv = ["dbus-virtual-battery.py", "--smartshunt-index", "1"]
main()
assert factory.call_args.kwargs["smartshunt_index"] == 1
"""
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            smoke,
            str(root),
            str(ROOT / "tests/fake_dbus.py"),
            TAG.removeprefix("v"),
        ],
        cwd=tmp_path,
        check=True,
    )


def test_release_tag_must_match_version(tmp_path):
    """Prevent publication under a tag that disagrees with installer metadata."""
    with pytest.raises(ValueError, match="committed version"):
        build_archive(ROOT, "v0.0.0", tmp_path)
