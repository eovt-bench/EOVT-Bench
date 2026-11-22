#!/usr/bin/env python3
"""Validate/install separately acquired simulation resources."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def valid_file(path: Path, item: dict) -> bool:
    return (
        path.is_file() and path.stat().st_size == item["bytes"]
        and file_hash(path) == item["sha256"]
    )


def attachment_path(directory: Path, name: str) -> Path:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError("Attachment filename must be a plain filename")
    return directory / name


def assemble_parts(directory: Path, item: dict, output: Path) -> Path:
    """Join parts in manifest order; publish the archive only after full checks."""
    if valid_file(output, item):
        return output
    parts = item.get("parts", [])
    if not parts or len({part["filename"] for part in parts}) != len(parts):
        raise ValueError("Missing or duplicate resource parts")
    sources = [attachment_path(directory, part["filename"]) for part in parts]
    for source, part in zip(sources, parts):
        if not valid_file(source, part):
            raise ValueError(f"Part size/SHA-256 mismatch: {part['filename']}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".joined-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            for source in sources:
                with source.open("rb") as reader:
                    shutil.copyfileobj(reader, handle)
        except Exception:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    if not valid_file(temporary, item):
        temporary.unlink(missing_ok=True)
        raise ValueError("Assembled archive size/SHA-256 mismatch")
    temporary.replace(output)
    return output


def download_archive(directory: Path, item: dict, config: dict, workers: int = 4) -> Path:
    """Cache completed attachments so interrupted downloads can reuse them."""
    if item.get("delivery", "release_attachment") != "release_attachment":
        raise ValueError("External resources cannot be downloaded from this Release; see docs/THIRD_PARTY_RESOURCES.md")
    directory.mkdir(parents=True, exist_ok=True)
    output = attachment_path(directory, item["filename"])
    if valid_file(output, item):
        return output

    def fetch(entry):
        target = attachment_path(directory, entry["filename"])
        if valid_file(target, entry):
            return
        with tempfile.TemporaryDirectory(prefix="download-", dir=directory) as folder:
            subprocess.run([
                "gh", "release", "download", config["release_tag"],
                "--repo", config["repository"], "--pattern", entry["filename"], "--dir", folder,
            ], check=True)
            incoming = Path(folder) / entry["filename"]
            if not valid_file(incoming, entry):
                raise ValueError(f"Downloaded size/SHA-256 mismatch: {entry['filename']}")
            incoming.replace(target)

    entries = item.get("parts") or [item]
    with ThreadPoolExecutor(max_workers=min(workers, len(entries))) as pool:
        list(pool.map(fetch, entries))
    if item.get("parts"):
        return assemble_parts(directory, item, output)
    return output


def install(archive: Path, item: dict, overwrite: bool):
    if archive.stat().st_size != item["bytes"] or file_hash(archive) != item["sha256"]:
        raise ValueError("Archive size/SHA-256 mismatch; installation aborted.")
    manifest = json.loads((ROOT / item["manifest"]).read_text(encoding="utf-8"))
    expected = {entry["path"]: entry for entry in manifest["files"]}
    seen = set()
    # Validate the complete archive before changing the working directory.
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle:
            parts = PurePosixPath(member.name).parts
            if not parts or ".." in parts or PurePosixPath(member.name).is_absolute():
                raise ValueError("Unexpected archive path")
            if member.isdir():
                continue
            name = "/".join(parts)
            if not member.isfile() or name not in expected or name in seen or member.size != expected[name]["bytes"]:
                raise ValueError(f"Unexpected archive member: {name}")
            target = ROOT.joinpath(*parts).resolve()
            if not target.is_relative_to(ROOT):
                raise ValueError("Resource path escapes repository")
            if target.exists() and not overwrite and file_hash(target) != expected[name]["sha256"]:
                raise ValueError(f"Conflicting file: {name}; use --overwrite only if replacement is intended")
            seen.add(name)
    if seen != set(expected):
        raise ValueError("Archive is incomplete")
    count = 0
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle:
            if not member.isfile():
                continue
            name = "/".join(PurePosixPath(member.name).parts)
            target = ROOT.joinpath(*PurePosixPath(name).parts)
            if target.is_file() and file_hash(target) == expected[name]["sha256"]:
                count += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".resource-", delete=False) as output:
                temporary = Path(output.name)
                try:
                    with bundle.extractfile(member) as source:
                        shutil.copyfileobj(source, output)
                except Exception:
                    output.close()
                    temporary.unlink(missing_ok=True)
                    raise
            if file_hash(temporary) != expected[name]["sha256"]:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"Extracted checksum mismatch: {name}")
            temporary.replace(target)
            count += 1
    print(f"Verified and installed {count} resource files.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("assets",), required=True)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--archive", type=Path, help="Install an existing complete archive")
    source.add_argument("--parts-dir", type=Path, help="Assemble manually downloaded resource parts")
    parser.add_argument("--workers", type=int, default=4, help="Parallel attachment downloads (default: 4)")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    config = json.loads((ROOT / "downloads.json").read_text(encoding="utf-8"))
    item = config["resources"][args.kind]
    if item.get("delivery") == "external_manual":
        if args.parts_dir:
            parser.error("Mixed asset parts have been withdrawn; acquire resources separately. See docs/THIRD_PARTY_RESOURCES.md")
        if not args.archive:
            parser.error(
                "Simulation assets are not hosted by this Release. "
                "Follow docs/THIRD_PARTY_RESOURCES.md and run scripts/check_resources.py. "
                "An already lawfully obtained matching local archive can be installed with --archive."
            )
        # Compatibility with existing users' local archives, without providing
        # a download URL or bypassing the resource owner's access conditions.
        compatibility = item["local_archive_compatibility"]
        install(args.archive.expanduser().resolve(), {
            **compatibility, "manifest": item["manifest"],
        }, args.overwrite)
        return
    if args.archive:
        install(args.archive.expanduser().resolve(), item, args.overwrite)
        return
    downloads = ROOT / ".downloads" / config["version"]
    if args.parts_dir:
        if not item.get("parts"):
            parser.error("This resource has no multipart attachments; use --archive")
        archive = assemble_parts(
            args.parts_dir.expanduser().resolve(), item,
            attachment_path(downloads, item["filename"]),
        )
        install(archive, item, args.overwrite)
        return
    if not shutil.which("gh"):
        parser.error("Authenticate GitHub CLI first, or supply --archive / --parts-dir.")
    archive = download_archive(downloads, item, config, args.workers)
    install(archive, item, args.overwrite)


if __name__ == "__main__":
    main()
