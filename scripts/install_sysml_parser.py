#!/usr/bin/env python3
"""Install the pinned OMG SysML v2 pilot parser into this repository's ignored cache."""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "sysml"
ARCHIVE = CACHE / "jupyter-sysml-kernel-0.52.0.zip"
URL = "https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/2025-09/jupyter-sysml-kernel-0.52.0.zip"
SHA256 = "c59342cb8ff5cbf9402a4df7ea3b47108078904802718792699ad854a78a3c32"
PILOT = CACHE / "pilot-2025-09"
JAR = PILOT / "sysml" / "jupyter-sysml-kernel-0.52.0-all.jar"
LIBRARY = PILOT / "sysml" / "sysml.library"
CLASSES = CACHE / "classes"
SOURCE = ROOT / "tools" / "sysml" / "SysmlBridge.java"
SOURCE_STAMP = CLASSES / "SysmlBridge.source.sha256"


def digest(path):
    result = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        partial = ARCHIVE.with_suffix(".partial")
        try:
            with urlopen(URL, timeout=60) as source, partial.open("wb") as target:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(block)
            partial.replace(ARCHIVE)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    actual = digest(ARCHIVE)
    if actual != SHA256:
        print(f"Parser archive SHA-256 mismatch: {actual}", file=sys.stderr)
        return 1
    if not JAR.exists() or not LIBRARY.exists():
        with ZipFile(ARCHIVE) as archive:
            for member in archive.infolist():
                if member.filename not in {"LICENSE", "LICENSE-GPL"} and not member.filename.startswith("sysml/"):
                    continue
                target = (PILOT / member.filename).resolve()
                if not target.is_relative_to(PILOT.resolve()):
                    print("Unsafe archive path", file=sys.stderr)
                    return 1
                archive.extract(member, PILOT)
    CLASSES.mkdir(exist_ok=True)
    build = subprocess.run(["javac", "-cp", str(JAR), "-d", str(CLASSES), str(SOURCE)], check=False)
    if build.returncode:
        return build.returncode
    SOURCE_STAMP.write_text(digest(SOURCE) + "\n")
    print(f"Installed OMG SysML v2 Pilot 2025-09 ({actual})")
    print(f"Parser: {JAR}")
    print(f"Libraries: {LIBRARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
