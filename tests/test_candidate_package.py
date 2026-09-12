"""Exercise the native candidate adapter without device connections or publication."""

import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

import pytest

from scripts.package_release import build_package


@pytest.fixture(name="package_source")
def fixture_package_source(tmp_path: Path) -> Path:
    """Create a tracked runtime plus untracked device-local configuration."""
    root = tmp_path / "source"
    root.mkdir()
    (root / "runtime.py").write_text('print("runtime")\n', encoding="utf-8")
    (root / "setup").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (root / "setup").chmod(0o755)
    (root / "version").write_text("1.2.3\n", encoding="utf-8")
    (root / ".release-policy.json").write_text(
        json.dumps({"version_file": "version"}), encoding="utf-8"
    )
    (root / ".release-package.json").write_text(
        json.dumps({"name": "fixture", "include": ["runtime.py", "setup", "version"]}),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    (root / "local_config.py").write_text("DEVICE_LOCAL = True\n", encoding="utf-8")
    return root


def test_native_bytes_modes_checksums_and_repeatability(
    package_source: Path, tmp_path: Path
) -> None:
    """Only tracked runtime inputs enter reproducible archives with executable setup."""
    first = build_package(package_source, "1.2.3", "rc", tmp_path / "first")[0]
    second = build_package(package_source, "1.2.3", "rc", tmp_path / "second")[0]
    assert first.read_bytes() == second.read_bytes()
    assert (first.parent / "SHA256SUMS").read_text().split()[0] == hashlib.sha256(
        first.read_bytes()
    ).hexdigest()
    with tarfile.open(first) as archive:
        assert archive.getnames() == [
            "fixture/runtime.py",
            "fixture/setup",
            "fixture/version",
        ]
        assert archive.getmember("fixture/setup").mode == 0o755
        version = archive.extractfile("fixture/version")
        assert version is not None and version.read() == b"1.2.3\n"


@pytest.mark.parametrize(
    ("version", "channel", "message"),
    [
        ("../../unsafe", "rc", "semantic version"),
        ("1.2.4", "rc", "committed project metadata"),
        ("1.2.3", "invalid", "release channel"),
    ],
)
def test_candidate_identity_is_validated(
    package_source: Path, tmp_path: Path, version: str, channel: str, message: str
) -> None:
    """Reject path-like versions, wrong source versions and unknown channels."""
    with pytest.raises(ValueError, match=message):
        build_package(package_source, version, channel, tmp_path / "output")


def test_stale_output_is_rejected(package_source: Path, tmp_path: Path) -> None:
    """A previous build cannot silently contribute artifacts to a new candidate."""
    output = tmp_path / "output"
    build_package(package_source, "1.2.3", "rc", output)
    with pytest.raises(ValueError, match="must be empty"):
        build_package(package_source, "1.2.3", "rc", output)


def test_missing_runtime_is_rejected(package_source: Path, tmp_path: Path) -> None:
    """Every declared runtime input must remain present in the tracked checkout."""
    (package_source / "runtime.py").unlink()
    with pytest.raises(ValueError, match="Missing required runtime input"):
        build_package(package_source, "1.2.3", "rc", tmp_path / "output")


def test_runtime_symlink_is_rejected(package_source: Path, tmp_path: Path) -> None:
    """A tracked symlink cannot pull untracked local configuration into an archive."""
    (package_source / "runtime.py").unlink()
    (package_source / "runtime.py").symlink_to(package_source / "local_config.py")
    with pytest.raises(ValueError, match="non-regular runtime input"):
        build_package(package_source, "1.2.3", "rc", tmp_path / "output")


def test_source_distribution_excludes_deleted_and_untracked_inputs(
    package_source: Path, tmp_path: Path
) -> None:
    """Source packaging uses surviving tracked files and never device-local inputs."""
    (package_source / ".release-package.json").write_text(
        json.dumps({"name": "fixture", "source": True}), encoding="utf-8"
    )
    (package_source / "runtime.py").unlink()
    archive_path = build_package(
        package_source, "1.2.3", "nightly", tmp_path / "output"
    )[0]
    with tarfile.open(archive_path) as archive:
        assert "fixture/version" in archive.getnames()
        assert "fixture/runtime.py" not in archive.getnames()
        assert "fixture/local_config.py" not in archive.getnames()
