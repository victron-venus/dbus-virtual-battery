"""Stage actual package bytes while rejecting paths that escape DESTDIR."""

import json
from pathlib import Path

import pytest

from install import MANIFEST, PAYLOAD, package_path, stage, unstage

SOURCE = Path(__file__).resolve().parents[1]


def test_staging_preserves_modes_and_operator_files(tmp_path):
    destination = tmp_path / "staging"
    stage(SOURCE, str(destination))
    package = package_path(str(destination))
    assert (package / "dbus-virtual-battery.py").read_bytes() == (
        SOURCE / "dbus-virtual-battery.py"
    ).read_bytes()
    assert (package / "setup").stat().st_mode & 0o111
    assert set(json.loads((package / MANIFEST).read_text())) == set(PAYLOAD)
    (package / "local_config.py").write_text("LOCAL = True\n")
    unstage(str(destination))
    assert [p.name for p in package.iterdir()] == ["local_config.py"]


@pytest.mark.parametrize("destination", ["", "/"])
def test_staging_rejects_live_root(destination):
    with pytest.raises(ValueError, match="DESTDIR"):
        package_path(destination)


def test_staging_rejects_symlink_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = tmp_path / "staging"
    destination.mkdir()
    (destination / "data").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        stage(SOURCE, str(destination))
    assert list(outside.iterdir()) == []


def test_staging_rejects_hardlinked_destination(tmp_path):
    destination = tmp_path / "staging"
    package = package_path(str(destination))
    package.mkdir(parents=True)
    protected = tmp_path / "protected"
    protected.write_text("unchanged")
    (package / "setup").hardlink_to(protected)
    with pytest.raises(ValueError, match="hardlinks"):
        stage(SOURCE, str(destination))
    assert protected.read_text() == "unchanged"


def test_uninstall_rejects_manifest_escape(tmp_path):
    destination = tmp_path / "staging"
    stage(SOURCE, str(destination))
    package = package_path(str(destination))
    (package / MANIFEST).write_text('["../../protected"]')
    with pytest.raises(ValueError, match="manifest"):
        unstage(str(destination))
    assert (package / "setup").exists()


def test_empty_staged_package_is_removed(tmp_path):
    destination = str(tmp_path / "staging")
    stage(SOURCE, destination)
    unstage(destination)
    assert not package_path(destination).exists()
