"""Build the complete SetupHelper archive without accessing a device."""

import argparse
import gzip
import hashlib
import io
import re
import tarfile
from pathlib import Path


def build_archive(root: Path, tag: str, output: Path) -> Path:
    """Package explicit runtime inputs with reproducible metadata and a checksum."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?|nightly", tag):
        raise ValueError("Expected a semantic version tag or nightly")
    if tag != "nightly" and (root / "version").read_text().strip() != tag:
        raise ValueError("Release tag must match the committed version file")
    paths = [
        root / name
        for name in ("dbus-virtual-battery.py", "setup", "gitHubInfo", "version")
    ]
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"dbus-virtual-battery-{tag}.tar.gz"
    with (
        archive.open("wb") as destination,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=destination, mtime=0
        ) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as package,
    ):
        for path in sorted(paths):
            content = path.read_bytes()
            entry = tarfile.TarInfo(f"dbus-virtual-battery/{path.relative_to(root)}")
            entry.size = len(content)
            entry.mode = 0o755 if path.name == "setup" else 0o644
            package.addfile(entry, io.BytesIO(content))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{digest}  {archive.name}\n"
    )
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    print(build_archive(repository, args.tag, repository / "dist"))
