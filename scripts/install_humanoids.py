#!/usr/bin/env python3
"""Install checksum-pinned actor files from the separately acquired humanoids.zip."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from check_resources import file_hash

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "assets/humanoids/humanoid_data/"
ARCHIVE_PREFIX = "humanoids/humanoid_data/"


def install(archive: Path, *, overwrite=False, check_only=False):
    inventory = json.loads((ROOT / "assets/manifest.json").read_text())
    expected = [entry for entry in inventory["files"] if entry["path"].startswith(PREFIX)]
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP members")
        # Validate all required files before writing any. Only pinned actors
        # are installed; bundled metadata and macOS sidecars are never copied.
        for entry in expected:
            member = ARCHIVE_PREFIX + entry["path"][len(PREFIX):]
            info = bundle.getinfo(member)
            if info.file_size != entry["bytes"]:
                raise ValueError("Actor file size mismatch: " + member)
            digest = hashlib.sha256()
            with bundle.open(info) as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != entry["sha256"]:
                raise ValueError("Actor checksum mismatch: " + member)
            target = (ROOT / entry["path"]).resolve()
            if not target.is_relative_to((ROOT / PREFIX).resolve()):
                raise ValueError("Actor path escapes destination")
            if target.exists() and file_hash(target) != entry["sha256"] and not overwrite:
                raise ValueError("Conflicting file; replacement requires --overwrite: " + entry["path"])
        if not check_only:
            for entry in expected:
                target = ROOT / entry["path"]
                if target.is_file() and file_hash(target) == entry["sha256"]:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                member = ARCHIVE_PREFIX + entry["path"][len(PREFIX):]
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as destination:
                    temporary = Path(destination.name)
                    try:
                        with bundle.open(member) as source:
                            for block in iter(lambda: source.read(1024 * 1024), b""):
                                destination.write(block)
                    except BaseException:
                        destination.close()
                        temporary.unlink(missing_ok=True)
                        raise
                if file_hash(temporary) != entry["sha256"]:
                    temporary.unlink(missing_ok=True)
                    raise ValueError("File changed during extraction: " + member)
                temporary.replace(target)
    print(json.dumps({"status": "PASS", "verified_files": len(expected),
                      "installed": not check_only, "metadata_replaced": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    install(args.archive.expanduser().resolve(), overwrite=args.overwrite, check_only=args.check_only)


if __name__ == "__main__":
    main()
