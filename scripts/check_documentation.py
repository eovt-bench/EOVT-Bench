#!/usr/bin/env python3
"""Check local Markdown link/image targets against the public source inventory."""
from __future__ import annotations

import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def source_paths():
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True, capture_output=True,
        )
        return set(filter(None, result.stdout.decode("utf-8").split("\0")))
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    return {entry["path"] for entry in manifest["files"]}


class HTMLTargets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and (tag, key) in {("a", "href"), ("img", "src")}:
                self.targets.append(value)


def link_targets(text):
    """Ignore code examples and recognize inline, reference and HTML targets."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
            continue
        if fence is None and not line.startswith(("    ", "\t")):
            lines.append(line)
    prose = "\n".join(lines)
    prose = re.sub(r"(`+).*?\1", "", prose)
    inline = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)\n]+)", prose)
    references = re.findall(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|[^\s\n]+)", prose, re.M)
    html = HTMLTargets()
    html.feed(prose)
    return [target.strip("<>") for target in inline + references + html.targets]


def main():
    names = source_paths()
    documents = sorted(name for name in names if name.lower().endswith(".md"))
    errors = []
    checked = 0
    for name in documents:
        source = ROOT / name
        for target in link_targets(source.read_text(encoding="utf-8")):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            checked += 1
            path = unquote(parsed.path)
            resolved = (
                ROOT / path.lstrip("/") if path.startswith("/") else source.parent / path
            ).resolve()
            if not resolved.is_relative_to(ROOT):
                errors.append({"file": name, "target": target, "reason": "outside repository"})
                continue
            relative = resolved.relative_to(ROOT).as_posix()
            published = relative in names or any(
                item.startswith(relative.rstrip("/") + "/") for item in names
            )
            if not resolved.exists() or not published:
                errors.append({
                    "file": name, "target": target,
                    "reason": "target missing from public source",
                })
    report = {
        "status": "FAIL" if errors else "PASS",
        "markdown_files": len(documents),
        "local_targets_checked": checked,
        "scope": "Local file/image targets; remote URLs and fragment anchors are not checked.",
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
