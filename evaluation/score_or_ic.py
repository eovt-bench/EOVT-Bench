"""Command-line entry points for the versioned OR and IC scorers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ic_behavior import score_event as score_ic
from or_visibility import score_event as score_or


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score EOVT initial OR/IC protocol evidence.")
    sub = parser.add_subparsers(dest="task", required=True)

    or_parser = sub.add_parser("or", help="score a JSON list of synchronized OR records")
    or_parser.add_argument("input", type=Path)
    or_parser.add_argument("--output", type=Path)

    ic_parser = sub.add_parser("ic", help="score one IC event JSON object")
    ic_parser.add_argument("input", type=Path)
    ic_parser.add_argument("--output", type=Path)

    args = parser.parse_args()
    payload = _read_json(args.input)
    if args.task == "or":
        if isinstance(payload, dict):
            payload = payload.get("records", payload.get("frames", payload))
        if not isinstance(payload, list):
            raise SystemExit("OR input must be a JSON list or an object containing records/frames")
        result = score_or(payload)
    else:
        if not isinstance(payload, dict):
            raise SystemExit("IC input must be a JSON object with same and similar trials")
        result = score_ic(payload)
    if args.output:
        _write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
