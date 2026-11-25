from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "baselines"))

from eovt_baseline.paths import resolve_readonly  # noqa: E402
from eovt_baseline.result_schema import validate_result  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--task", choices=("stt", "or", "ic"))
    args = parser.parse_args()
    root = Path(args.path).expanduser().resolve()
    valid = invalid = 0
    for path in root.rglob("*.json"):
        if (path.name.endswith("_info.json") or "status" in path.name.lower()
                or any(part.endswith("_evidence") for part in path.relative_to(root).parts[:-1])):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_result(data, args.task)
        except Exception as exc:
            errors = [repr(exc)]
        if errors:
            invalid += 1
            print(f"INVALID {path}: {'; '.join(errors)}")
        else:
            valid += 1
    print(f"valid={valid} invalid={invalid}")
    return 0 if invalid == 0 and valid > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

