from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eovt_baseline.paths import resolve_readonly  # noqa: E402
from eovt_baseline.result_schema import validate_result  # noqa: E402


METRICS = (
    "success", "following_rate", "collision",
    "reacquisition_success", "visibility_opportunity", "conditional_reacquisition", "recovery_steps",
    "same_success_rate", "similar_success_rate",
    "swap_success_rate", "similar_swap_success", "balanced_identity_accuracy",
)


def bootstrap_cluster(rows, key, metric, iterations, seed):
    groups = defaultdict(list)
    for row in rows:
        if row.get(key) is not None and isinstance(row.get(metric), (int, float)):
            groups[str(row[key])].append(float(row[metric]))
    labels = list(groups)
    if not labels:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        chosen = [rng.choice(labels) for _ in labels]
        values = [value for label in chosen for value in groups[label]]
        samples.append(mean(values))
    samples.sort()
    lo = samples[int(0.025 * (len(samples) - 1))]
    hi = samples[int(0.975 * (len(samples) - 1))]
    return [lo, hi]


def bootstrap_values(values, iterations, seed):
    if not values:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        samples.append(mean(rng.choice(values) for _ in values))
    samples.sort()
    return [samples[int(0.025 * (len(samples) - 1))], samples[int(0.975 * (len(samples) - 1))]]


def wilson(values):
    if not values:
        return None
    p = mean(values)
    n = len(values)
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--cluster-key")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    root = resolve_readonly(args.path)
    rows = []
    for path in root.rglob("*.json"):
        if path.name.endswith("_info.json"):
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not validate_result(row):
            rows.append(row)
    report = {"path": str(root), "valid_results": len(rows), "metrics": {}}
    for metric in METRICS:
        values = [float(row[metric]) for row in rows if isinstance(row.get(metric), (int, float))]
        if not values:
            continue
        entry = {"n": len(values), "mean": mean(values)}
        entry["episode_bootstrap_95"] = bootstrap_values(values, args.bootstrap, args.seed)
        if all(value in (0.0, 1.0) for value in values):
            entry["wilson_95"] = wilson(values)
        if args.cluster_key:
            entry["cluster_bootstrap_95"] = bootstrap_cluster(rows, args.cluster_key, metric, args.bootstrap, args.seed)
        report["metrics"][metric] = entry
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

