#!/usr/bin/env python3
"""Check the public source inventory; --write refreshes hashes of staged/tracked paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"MANIFEST.json", "SHA256SUMS"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_paths(root):
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], check=True, capture_output=True,
    )
    return sorted(p for p in completed.stdout.decode("utf-8").split("\0") if p)


def refresh():
    paths = tracked_paths(ROOT)
    version = (ROOT / "VERSION").read_text().strip()
    manifest = {
        "version": version,
        "resource_policy_version": json.loads(
            (ROOT / "assets/resource_policy.json").read_text(encoding="utf-8")
        )["policy_version"],
        "distribution_update": "2026-11-25",
        "scope": "Git source and compact metadata; separately installed assets are excluded.",
        "excluded_from_manifest": sorted(EXCLUDED),
        "files": [
            {"path": name, "bytes": (ROOT / name).stat().st_size, "sha256": digest(ROOT / name)}
            for name in paths if name not in EXCLUDED
        ],
    }
    (ROOT / "MANIFEST.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    (ROOT / "SHA256SUMS").write_bytes(
        "".join(f"{digest(ROOT / name)}  {name}\n" for name in paths if name != "SHA256SUMS").encode("utf-8")
    )


def verify(root=ROOT):
    errors = []
    manifest = json.loads((root / "MANIFEST.json").read_text())
    paths = [item["path"] for item in manifest["files"]]
    if len(paths) != len(set(paths)):
        errors.append("duplicate manifest paths")
    if manifest["version"] != (root / "VERSION").read_text().strip():
        errors.append("manifest version differs from VERSION")
    for item in manifest["files"]:
        name = item["path"]
        parts = PurePosixPath(name)
        target = (root / name).resolve()
        if parts.is_absolute() or ".." in parts.parts or not target.is_relative_to(root.resolve()):
            errors.append("unsafe manifest path")
            continue
        if not target.is_file():
            errors.append("missing: " + name)
        elif target.stat().st_size != item["bytes"] or digest(target) != item["sha256"]:
            errors.append("changed: " + name)
    # A Git checkout can also prove that new public files were not omitted.
    if (root / ".git").exists():
        expected = set(tracked_paths(root)) - EXCLUDED
        if set(paths) != expected:
            errors.append("manifest coverage differs from tracked source")
    sums = {}
    for line in (root / "SHA256SUMS").read_text().splitlines():
        checksum, name = line.split("  ", 1)
        if name in sums:
            errors.append("duplicate SHA256SUMS path: " + name)
        sums[name] = checksum
    if set(sums) != set(paths) | {"MANIFEST.json"}:
        errors.append("SHA256SUMS coverage differs from manifest")
    for name, checksum in sums.items():
        parts = PurePosixPath(name)
        target = (root / name).resolve()
        if parts.is_absolute() or ".." in parts.parts or not target.is_relative_to(root.resolve()):
            errors.append("unsafe checksum path")
        elif not target.is_file() or digest(target) != checksum:
            errors.append("checksum mismatch: " + name)
    return {"status": "FAIL" if errors else "PASS", "files": len(paths),
            "version": manifest["version"], "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Refresh after staging intended source files")
    args = parser.parse_args()
    if args.write:
        refresh()
    report = verify()
    print(json.dumps(report, indent=2))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
