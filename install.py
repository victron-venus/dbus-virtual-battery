"""Stage the Venus OS payload without contacting or starting a device service.

Adapted from the MIT-licensed inverter-control staging installer.
"""

import argparse
import json
import os
import shutil
from pathlib import Path

PAYLOAD = (
    "dbus-virtual-battery.py",
    "setup",
    "gitHubInfo",
    "version",
    "install.sh",
    "install.py",
    "requirements.txt",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    ".python-version",
    "uv.lock",
)
MANIFEST = ".installed-files.json"


def reject_links(path: Path) -> None:
    """Reject existing links before writing into an operator-owned staging tree."""
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise ValueError(f"Staging paths must not contain symlinks: {component}")
        if component.is_file() and component.stat().st_nlink > 1:
            raise ValueError(f"Staging paths must not contain hardlinks: {component}")


def package_path(destdir: str) -> Path:
    """Require an explicit non-root destination; never install on the live host."""
    if not destdir:
        raise ValueError("DESTDIR must select a non-root staging directory")
    root = Path(os.path.abspath(destdir))
    if root == Path(root.anchor):
        raise ValueError("DESTDIR must not be the live filesystem root")
    package = root / "data/dbus-virtual-battery"
    reject_links(package)
    return package


def stage(source: Path, destdir: str) -> None:
    """Copy a fixed payload and preserve executable modes, excluding local config."""
    package = package_path(destdir)
    for name in PAYLOAD:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or non-regular package input: {name}")
    for name in (*PAYLOAD, MANIFEST):
        reject_links(package / name)
    package.mkdir(parents=True, exist_ok=True)
    for name in PAYLOAD:
        path, target = source / name, package / name
        shutil.copyfile(path, target)
        target.chmod(0o755 if path.stat().st_mode & 0o111 else 0o644)
    (package / MANIFEST).write_text(json.dumps(list(PAYLOAD), indent=2) + "\n")


def unstage(destdir: str) -> None:
    """Remove only manifest-listed payload files; preserve operator-owned files."""
    package = package_path(destdir)
    reject_links(package / MANIFEST)
    names = json.loads((package / MANIFEST).read_text())
    if not isinstance(names, list) or not all(
        isinstance(name, str) and name in PAYLOAD for name in names
    ):
        raise ValueError("Invalid staged installation manifest")
    for name in names:
        reject_links(package / name)
    for name in names:
        (package / name).unlink(missing_ok=True)
    (package / MANIFEST).unlink()
    if not any(package.iterdir()):
        package.rmdir()


def main() -> None:
    """Implement conventional DESTDIR installation without implicit activation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("install", "uninstall"), nargs="?", default="install"
    )
    parser.add_argument("--destdir", default=os.environ.get("DESTDIR", ""))
    args = parser.parse_args()
    if args.action == "install":
        stage(Path(__file__).resolve().parent, args.destdir)
    else:
        unstage(args.destdir)


if __name__ == "__main__":
    main()
