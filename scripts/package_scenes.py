#!/usr/bin/env python3
"""Package only the author-constructed, checksum-pinned scene resource group."""
from __future__ import annotations

import argparse
import gzip
import json
import tarfile
from pathlib import Path

from check_resources import audit_resources, file_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Output already exists; use a new explicit filename")
    report = audit_resources(group="scenes")
    if report["status"] != "PASS":
        raise ValueError("Installed scenes do not match the experiment inventory")
    inventory = json.loads((ROOT / "assets/scenes_manifest.json").read_text())
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    try:
        with temporary.open("wb") as raw, gzip.GzipFile(
            filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=6
        ) as compressed, tarfile.open(fileobj=compressed, mode="w|") as bundle:
            for entry in inventory["files"]:
                source = ROOT / entry["path"]
                if not entry["path"].startswith("scenes/layout_instances/"):
                    raise ValueError("Standalone scenes must not include third-party actors or weights")
                member = bundle.gettarinfo(str(source), arcname=entry["path"])
                if not member.isfile() or file_hash(source) != entry["sha256"]:
                    raise ValueError("Scene changed during packaging: " + entry["path"])
                member.mtime = member.uid = member.gid = 0
                member.uname = member.gname = ""
                member.mode = 0o644
                with source.open("rb") as handle:
                    bundle.addfile(member, handle)
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    print(json.dumps({
        "filename": output.name, "bytes": output.stat().st_size,
        "sha256": file_hash(output), "files": len(inventory["files"]),
        "manifest": "assets/scenes_manifest.json",
    }, indent=2))


if __name__ == "__main__":
    main()
