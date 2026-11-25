from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eovt_baseline.paths import resolve_readonly  # noqa: E402
from eovt_baseline.result_schema import valid_final_result  # noqa: E402


def snapshot(root: Path) -> str:
    files = [path for path in root.rglob("*.json") if valid_final_result(path)]
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    def avg(key):
        values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
        return "N/A" if not values else f"{100 * sum(values) / len(values):.2f}%"
    lines = [
        "EOVT-Bench baseline live monitor",
        f"path: {root}",
        f"completed: {len(rows)}",
        f"SR={avg('success')}  TR={avg('following_rate')}  CR={avg('collision')}",
    ]
    if any("reacquisition_success" in row for row in rows):
        lines.append(f"RSR={avg('reacquisition_success')}  VOR={avg('visibility_opportunity')}  CRR={avg('conditional_reacquisition')}")
    if any("balanced_identity_accuracy" in row for row in rows):
        similar_key = (
            "similar_success_rate" if any("similar_success_rate" in row for row in rows)
            else ("similar_swap_success" if any("similar_swap_success" in row for row in rows) else "swap_success_rate")
        )
        lines.append(f"SameSR={avg('same_success_rate')}  SimilarSR={avg(similar_key)}  BIA={avg('balanced_identity_accuracy')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    root = resolve_readonly(args.path)
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(snapshot(root), flush=True)
        if args.once:
            return 0
        time.sleep(max(1.0, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
