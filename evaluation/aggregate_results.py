#!/usr/bin/env python3
"""Read-only common EOVT scorer with layout-cluster uncertainty."""
import argparse
import json
from pathlib import Path

from reporting import summarize_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--task", required=True, choices=("stt", "or", "ic"))
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261121)
    parser.add_argument("--output", type=Path, help="Optional summary JSON outside the input results")
    args = parser.parse_args()
    if args.bootstrap < 0:
        parser.error("--bootstrap must be nonnegative")
    results = args.results.expanduser().resolve()
    if args.output and args.output.expanduser().resolve().is_relative_to(results):
        parser.error("--output must be outside the input result directory")
    try:
        report = summarize_directory(results, args.task, args.bootstrap, args.seed)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    content = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
