#!/usr/bin/env python3
"""Offline stricter subsets of existing OR/IC events; no runtime changes."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
from pathlib import Path

import numpy as np

from shared_analysis import as_float, ic_event_metrics, load_json_records, summarize_ic, summarize_or

ROOT = Path(__file__).resolve().parents[1]
FILTERS = (
    ("original", 2.5, 0.5),
    ("pre_gt_3", 3.0, 0.5),
    ("occ_ge_1", 2.5, 1.0),
    ("pre_gt_3_occ_ge_1", 3.0, 1.0),
)


def bounds(values):
    finite = np.sort(values[np.isfinite(values)])
    if not len(finite):
        return None, None
    return float(finite[int(0.025 * (len(finite) - 1))]), float(finite[int(0.975 * (len(finite) - 1))])


def contribution(record, task, metric):
    data = record["data"]
    if task == "IC":
        point = ic_event_metrics([record])
        if metric == "rfr_pct":
            return point["same_failure_events"], point["effective_control_events"]
        return (point["dsr_pct"] / 100, 1) if point["dsr_pct"] is not None else (0, 0)
    if as_float(data.get("success")) is None:
        return 0, 0
    if metric == "crr":
        opportunity = as_float(data.get("vor"))
        recovered = as_float(data.get("rsr"))
        return (recovered, 1) if opportunity is not None and opportunity >= 0.5 and recovered is not None else (0, 0)
    value = as_float(data.get("recovery_steps" if metric == "mrs" else metric))
    return (value, 1) if value is not None else (0, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True, help="Root of your locally generated method results")
    parser.add_argument("--event-dataset", type=Path, default=ROOT / "episodes/OR/val/val.json.gz")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evaluation/outputs/event_filters")
    parser.add_argument("--methods", type=Path, help="Optional JSON mapping display names to method directories under results-root")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261121)
    args = parser.parse_args()
    if args.bootstrap < 1:
        parser.error("--bootstrap must be positive")
    results_root = args.results_root.resolve()
    output = args.output_dir.resolve()
    if output.is_relative_to(results_root):
        parser.error("Output must be outside original result files")
    output.mkdir(parents=True, exist_ok=True)
    plan = {
        "scope": "stricter subsets of existing events, without changing runtime actions or windows",
        "filters": [{"id": name, "pre_clear_gt_m": pre, "occlusion_ge_m": length} for name, pre, length in FILTERS],
        "bootstrap_unit": "layout", "repetitions": args.bootstrap, "seed": args.seed,
    }
    (output / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    episodes = json.loads(gzip.decompress(args.event_dataset.read_bytes()))["episodes"]
    metadata = {ep["episode_id"]: ep["info"]["eovt_task"] for ep in episodes}
    assert len(metadata) == len(episodes)
    layouts = sorted({meta["layout_id"] for meta in metadata.values()})
    layout_index = {layout: index for index, layout in enumerate(layouts)}
    methods = (
        json.loads(args.methods.read_text(encoding="utf-8"))
        if args.methods else {"RGB Tracker PID": "RGB_Tracker_PID", "Oracle PID": "Oracle_PID"}
    )
    rng = random.Random(args.seed)
    draws = np.zeros((args.bootstrap, len(layouts)), dtype=np.int32)
    for rep in range(args.bootstrap):
        for _ in layouts:
            draws[rep, rng.randrange(len(layouts))] += 1
    rows = []
    for method, folder in methods.items():
        for task in ("OR", "IC"):
            records, errors = load_json_records(results_root / folder / task / "json")
            if errors:
                raise ValueError(errors)
            mapped = {}
            for record in records:
                event_id = record["data"].get("episode_id") or record["path"].stem
                assert event_id in metadata and event_id not in mapped, event_id
                record["data"]["eovt_task"] = {**metadata[event_id], **(record["data"].get("eovt_task") or {})}
                mapped[event_id] = record
            assert set(mapped) == set(metadata), f"{method}/{task}: incomplete event coverage"
            metrics = ("rsr", "vor", "crr", "mrs") if task == "OR" else ("rfr_pct", "dsr_pct")
            original_values, original_replicates = {}, {}
            for name, pre, length in FILTERS:
                ids = sorted(event_id for event_id, meta in metadata.items()
                             if meta["pre_clear_length_m"] > pre and meta["event_arc_length_m"]["length"] >= length)
                selected = [mapped[event_id] for event_id in ids]
                summary = (summarize_or if task == "OR" else summarize_ic)(selected, 0, args.seed)
                for metric in metrics:
                    numerators, denominators = np.zeros(len(layouts)), np.zeros(len(layouts))
                    for event_id in ids:
                        numerator, denominator = contribution(mapped[event_id], task, metric)
                        index = layout_index[metadata[event_id]["layout_id"]]
                        numerators[index] += numerator
                        denominators[index] += denominator
                    scale = 1 if metric == "mrs" else 100
                    point = scale * numerators.sum() / denominators.sum() if denominators.sum() else None
                    expected = summary[metric]
                    assert (point is None and expected is None) or math.isclose(point, expected, rel_tol=1e-10, abs_tol=1e-9)
                    nums, dens = draws @ numerators, draws @ denominators
                    replicates = np.full(args.bootstrap, np.nan)
                    np.divide(scale * nums, dens, out=replicates, where=dens > 0)
                    if name == "original":
                        original_values[metric], original_replicates[metric] = expected, replicates
                    lo, hi = bounds(replicates)
                    delta_lo, delta_hi = bounds(replicates - original_replicates[metric])
                    rows.append({
                        "method": method, "task": task, "filter": name,
                        "events": len(ids), "layouts": len({metadata[i]["layout_id"] for i in ids}),
                        "metric": metric, "denominator": int(denominators.sum()),
                        "estimate": expected, "ci95_low": lo, "ci95_high": hi,
                        "delta_vs_original": expected - original_values[metric] if expected is not None and original_values[metric] is not None else None,
                        "delta_ci95_low": delta_lo, "delta_ci95_high": delta_hi,
                        "valid_bootstrap_repetitions": int(np.isfinite(replicates).sum()),
                    })
            print(f"Analyzed {method}/{task}", flush=True)
    with (output / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "README.md").write_text(
        "# Event-filter subset analysis\n\n"
        "Results: metrics.csv. The original event set is filtered using the four "
        "conditions in plan.json; runtime trial timing, actors, actions and metric "
        "definitions are unchanged. Percent metrics use percentage-point deltas; "
        "MRS uses step deltas. Identical 60-layout draws are paired across conditions. "
        "Subset composition and conditional denominators change, so differences "
        "are descriptive. This analysis does not test sampling density, runtime "
        "windows, or whether OTPR agrees with human identity judgments.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
