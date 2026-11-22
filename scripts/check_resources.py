#!/usr/bin/env python3
"""Read-only inventory/checksum check for separately acquired simulation resources."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_resources(root: Path = ROOT, group: str = "all", checksums: bool = True) -> dict:
    """Verify installed files; a matching checksum is not a license grant."""
    root = root.resolve()
    policy = json.loads((root / "assets/resource_policy.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "assets/manifest.json").read_text(encoding="utf-8"))
    groups = {entry["id"]: entry for entry in policy["groups"]}
    if group != "all" and group not in groups:
        raise ValueError(f"Unknown resource group: {group}")
    report = {
        "status": "PASS",
        "mode": "checksum" if checksums else "presence",
        "checked_files": 0,
        "groups": {},
        "inventory_errors": [],
        "note": "File checks do not establish acquisition or redistribution permission.",
    }
    for entry in manifest["files"]:
        name = entry["path"]
        parts = PurePosixPath(name)
        target = root.joinpath(*parts.parts).resolve()
        if parts.is_absolute() or ".." in parts.parts or "\\" in name or not target.is_relative_to(root):
            report["inventory_errors"].append(name)
            continue
        matching = [
            item for item in policy["groups"]
            if any(name == prefix.rstrip("/") or name.startswith(prefix.rstrip("/") + "/")
                   for prefix in item["paths"])
        ]
        if len(matching) != 1:
            report["inventory_errors"].append(name)
            continue
        definition = matching[0]
        key = definition["id"]
        if group != "all" and group != key:
            continue
        current = report["groups"].setdefault(key, {
            "delivery": definition["delivery"],
            "required_files": 0,
            "verified_files": 0,
            "missing": [],
            "mismatched": [],
            "instructions": definition["instructions"],
        })
        current["required_files"] += 1
        report["checked_files"] += 1
        if not target.is_file():
            current["missing"].append(name)
        elif target.stat().st_size != entry["bytes"]:
            current["mismatched"].append({"path": name, "reason": "size"})
        elif checksums and file_hash(target) != entry["sha256"]:
            current["mismatched"].append({"path": name, "reason": "sha256"})
        else:
            current["verified_files"] += 1
    if not report["checked_files"]:
        report["inventory_errors"].append("No matching inventory entries")
    if report["inventory_errors"] or any(
        item["missing"] or item["mismatched"] for item in report["groups"].values()
    ):
        report["status"] = "FAIL"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", default="all", help="all, metadata, scenes, humanoids, robot, detector")
    parser.add_argument("--presence-only", action="store_true", help="Skip hashes; still check file sizes")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable full report")
    args = parser.parse_args()
    try:
        report = audit_resources(group=args.group, checksums=not args.presence_only)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Resource check: {report['status']} ({report['mode']})")
        for key, entry in report["groups"].items():
            print(f"  {key}: {entry['verified_files']}/{entry['required_files']} verified; "
                  f"{len(entry['missing'])} missing; {len(entry['mismatched'])} mismatched")
        if report["inventory_errors"]:
            print("  Inventory errors: " + ", ".join(report["inventory_errors"][:5]))
        if report["status"] != "PASS":
            print("See docs/THIRD_PARTY_RESOURCES.md; no files were changed.")
        print(report["note"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
