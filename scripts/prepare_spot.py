#!/usr/bin/env python3
"""Reproduce the fixed benchmark robot from separately acquired official Spot files."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import urllib.request
from pathlib import Path

from check_resources import file_hash

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "assets/robots/hab_spot_arm/"


def download_source(source):
    manifest = json.loads((ROOT / "assets/spot_upstream_manifest.json").read_text())
    for entry in manifest["files"]:
        target = source / entry["path"]
        if target.exists():
            if target.stat().st_size == entry["bytes"] and file_hash(target) == entry["sha256"]:
                continue
            raise ValueError("Conflicting official source: " + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        url = (
            "https://huggingface.co/datasets/ai-habitat/hab_spot_arm/resolve/"
            + manifest["revision"] + "/" + entry["path"]
        )
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            try:
                with urllib.request.urlopen(url, timeout=90) as incoming:
                    for block in iter(lambda: incoming.read(1024 * 1024), b""):
                        output.write(block)
            except BaseException:
                output.close()
                temporary.unlink(missing_ok=True)
                raise
        if temporary.stat().st_size != entry["bytes"] or file_hash(temporary) != entry["sha256"]:
            temporary.unlink(missing_ok=True)
            raise ValueError("Official download checksum mismatch: " + entry["path"])
        temporary.replace(target)


def benchmark_bytes(name, content):
    """Preserve physics; reproduce the experiment's arm-visual omissions and CRLF."""
    if name not in {"LICENSE.txt", "README.md", "urdf/hab_spot_arm.urdf"}:
        return content
    text = content.decode("utf-8").replace("\r\n", "\n")
    if name.endswith(".urdf"):
        removed = 0

        def arm_link(match):
            nonlocal removed
            block, count = re.subn(
                r"(?ms)^    <visual>\n.*?^ ?</visual>\n", "", match.group(0)
            )
            removed += count
            return block

        text = re.sub(r'(?s)<link name="arm0\.[^"]+">.*?</link>', arm_link, text)
        if removed != 8:
            raise ValueError("Expected eight arm visual elements in the pinned upstream URDF")
    return text.replace("\n", "\r\n").encode("utf-8")


def prepare(source: Path, *, overwrite=False, check_only=False):
    upstream = json.loads((ROOT / "assets/spot_upstream_manifest.json").read_text())["files"]
    expected = {
        entry["path"][len(PREFIX):]: entry
        for entry in json.loads((ROOT / "assets/manifest.json").read_text())["files"]
        if entry["path"].startswith(PREFIX)
    }
    if set(expected) != {item["path"] for item in upstream}:
        raise ValueError("Upstream/benchmark robot inventories differ")
    converted = {}
    for item in upstream:
        name = item["path"]
        path = source / name
        if not path.is_file() or path.stat().st_size != item["bytes"] or file_hash(path) != item["sha256"]:
            raise ValueError("Official source mismatch: " + name)
        content = benchmark_bytes(name, path.read_bytes())
        entry = expected[name]
        if len(content) != entry["bytes"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError("Converted robot differs from the experiment: " + name)
        target = ROOT / PREFIX / name
        if target.exists() and file_hash(target) != entry["sha256"] and not overwrite:
            raise ValueError("Conflicting file; replacement requires --overwrite: " + name)
        converted[name] = content
    if not check_only:
        for name, content in converted.items():
            target = ROOT / PREFIX / name
            if target.is_file() and file_hash(target) == expected[name]["sha256"]:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
                temporary = Path(output.name)
                output.write(content)
            temporary.replace(target)
    print(json.dumps({"status": "PASS", "verified_files": len(converted),
                      "installed": not check_only, "removed_arm_visuals": 8,
                      "physics_or_sensor_configuration_changed": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Official hab_spot_arm directory")
    parser.add_argument("--download", action="store_true", help="Acquire pinned files directly from official HF")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    if args.download:
        download_source(source)
    prepare(source, overwrite=args.overwrite, check_only=args.check_only)


if __name__ == "__main__":
    main()
