#!/usr/bin/env python3
"""Reproducible EVT-Bench / OccBench result analysis.

The script only reads result JSON files. It does not modify model code or result
files. Outputs are CSV, Markdown, LaTeX, JSON, and a data-quality report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable


DEFAULT_SEED = 20260930
LAYOUT_RE = re.compile(r"^(.+?_layout_\d+_seed_\d{8})")


def as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def pct(value: float | None) -> float | None:
    return None if value is None else 100.0 * value


def mean_or_none(values: Iterable[float | None]) -> float | None:
    vals = [float(v) for v in values if v is not None]
    return mean(vals) if vals else None


def load_json_records(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    if not root.is_dir():
        errors.append({"path": str(root), "error": "missing_directory"})
        return records, errors
    for path in sorted(root.rglob("*.json")):
        if path.name.endswith("_info.json") or "status" in path.name.lower():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("top-level JSON value is not an object")
        except Exception as exc:  # Report malformed files without aborting all methods.
            errors.append({"path": str(path), "error": repr(exc)})
            continue
        records.append({"path": path, "data": data})
    return records, errors


def layout_id(record: dict[str, Any]) -> str:
    data = record["data"]
    meta = data.get("eovt_task") or {}
    if meta.get("layout_id"):
        return str(meta["layout_id"])
    if data.get("layout"):
        return str(data["layout"])
    episode_id = str(data.get("episode_id") or record["path"].stem)
    match = LAYOUT_RE.match(episode_id)
    return match.group(1) if match else episode_id.split("__", 1)[0]


def scene_id(record: dict[str, Any]) -> str:
    data = record["data"]
    meta = data.get("eovt_task") or {}
    if meta.get("scene_category"):
        return str(meta["scene_category"])
    path_parts = {part.lower() for part in record["path"].parts}
    for candidate in ("road", "indoor", "industrial"):
        if candidate in path_parts:
            return candidate
    episode_id = str(data.get("episode_id") or record["path"].stem).lower()
    return episode_id.split("_", 1)[0]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: Any, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out.extend("| " + " | ".join(fmt(cell) for cell in row) + " |" for row in rows)
    return "\n".join(out) + "\n"


def latex_table(caption: str, label: str, headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["\\begin{table}[t]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}"]
    lines.append("\\begin{tabular}{l" + "r" * (len(headers) - 1) + "}")
    lines.append("\\toprule")
    lines.append(" & ".join(headers) + " \\\\")
    lines.append("\\midrule")
    for row in rows:
        lines.append(" & ".join(fmt(cell) for cell in row) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    return "\n".join(lines)


def bootstrap_scalar(records: list[dict[str, Any]], statistic: Callable[[list[dict[str, Any]]], float | None], reps: int, seed: int) -> tuple[float | None, float | None]:
    """Cluster bootstrap by layout. Returns percentile 95% interval."""
    if reps <= 0 or not records:
        return None, None
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        clusters[layout_id(record)].append(record)
    keys = list(clusters)
    if not keys:
        return None, None
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(reps):
        sampled: list[dict[str, Any]] = []
        for _ in keys:
            sampled.extend(clusters[rng.choice(keys)])
        value = statistic(sampled)
        if value is not None and math.isfinite(value):
            values.append(value)
    if not values:
        return None, None
    values.sort()
    lo = values[max(0, int(0.025 * (len(values) - 1)))]
    hi = values[min(len(values) - 1, int(0.975 * (len(values) - 1)))]
    return lo, hi


def summarize_stt(records: list[dict[str, Any]], reps: int, seed: int) -> dict[str, Any]:
    def metric(name: str, rows: list[dict[str, Any]]) -> float | None:
        return pct(mean_or_none(as_float(r["data"].get(name)) for r in rows))

    result: dict[str, Any] = {"episodes": len(records), "valid": 0}
    valid = [r for r in records if as_float(r["data"].get("success")) is not None]
    result["valid"] = len(valid)
    for name, key in (("sr", "success"), ("tr", "following_rate"), ("cr", "collision")):
        value = metric(key, valid)
        lo, hi = bootstrap_scalar(valid, lambda rows, k=key: metric(k, rows), reps, seed)
        result[name] = value
        result[f"{name}_ci95_low"] = lo
        result[f"{name}_ci95_high"] = hi
    return result


def summarize_or(records: list[dict[str, Any]], reps: int, seed: int) -> dict[str, Any]:
    valid = [r for r in records if as_float(r["data"].get("success")) is not None]

    def statistic(rows: list[dict[str, Any]], key: str, nonnull_only: bool = False) -> float | None:
        values = [as_float(r["data"].get(key)) for r in rows]
        if nonnull_only:
            values = [v for v in values if v is not None]
        return pct(mean_or_none(values))

    def conditional_reacquisition(rows: list[dict[str, Any]]) -> float | None:
        outcomes: list[float] = []
        for row in rows:
            data = row["data"]
            visible = as_float(data.get("vor"))
            if visible is None:
                visible = as_float(data.get("visibility_opportunity"))
            if visible is None or visible < 0.5:
                continue
            recovered = as_float(data.get("rsr"))
            if recovered is None:
                recovered = as_float(data.get("reacquisition_success"))
            if recovered is not None:
                outcomes.append(recovered)
        return pct(mean_or_none(outcomes))

    result: dict[str, Any] = {"episodes": len(records), "valid": len(valid)}
    for name, key, nonnull in (("rsr", "rsr", False), ("vor", "vor", False)):
        value = statistic(valid, key, nonnull)
        lo, hi = bootstrap_scalar(valid, lambda rows, k=key, nn=nonnull: statistic(rows, k, nn), reps, seed)
        result[name] = value
        result[f"{name}_ci95_low"] = lo
        result[f"{name}_ci95_high"] = hi
    result["crr"] = conditional_reacquisition(valid)
    result["crr_ci95_low"], result["crr_ci95_high"] = bootstrap_scalar(
        valid, conditional_reacquisition, reps, seed
    )
    steps = [as_float(r["data"].get("recovery_steps")) for r in valid]
    steps = [v for v in steps if v is not None]
    result["mrs"] = mean(steps) if steps else None
    lo, hi = bootstrap_scalar(valid, lambda rows: mean_or_none(as_float(r["data"].get("recovery_steps")) for r in rows), reps, seed)
    result["mrs_ci95_low"] = lo
    result["mrs_ci95_high"] = hi
    return result


def trial_dominance(trial: dict[str, Any]) -> float | None:
    value = trial.get("target_dominance")
    if value is None:
        value = trial.get("target_dominance_rate")
    return as_float(value)


def ic_event_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    behavior_version = "eovt-ic-behavior-v0.1"
    if any(record["data"].get("identity_evaluator_version") == behavior_version for record in records):
        return _ic_behavior_event_metrics(records, behavior_version)

    same_valid = same_fail = same_success = same_collision = 0
    similar_valid = similar_collision = uncertain = switch = retain = 0
    event_rates: list[float] = []
    eligible_events = 0
    for record in records:
        data = record["data"]
        trials = data.get("identity_trial_results") or []
        if len(trials) != 4:
            continue
        same = [t for t in trials if t.get("condition") == "same"]
        similar = [t for t in trials if t.get("condition") in ("swap", "similar_swap")]
        if len(same) != 1 or len(similar) != 3:
            continue
        same_trial = same[0]
        if (as_float(same_trial.get("collision")) or 0.0) > 0:
            same_collision += 1
            continue
        if as_float(same_trial.get("success")) is None:
            continue
        same_valid += 1
        if (as_float(same_trial.get("success")) or 0.0) < 0.5:
            same_fail += 1
            continue
        same_success += 1
        event_errors: list[float] = []
        for trial in similar:
            if (as_float(trial.get("collision")) or 0.0) > 0:
                similar_collision += 1
                continue
            dominance = trial_dominance(trial)
            if dominance is None:
                continue
            similar_valid += 1
            if dominance < 0.5:
                switch += 1
                event_errors.append(1.0)
            elif dominance > 0.5:
                retain += 1
                event_errors.append(0.0)
            else:
                uncertain += 1
        if event_errors:
            eligible_events += 1
            event_rates.append(mean(event_errors))
    ofr = same_fail / same_valid if same_valid else None
    cier = mean(event_rates) if event_rates else None
    decisive = switch + retain
    trial_cier = switch / decisive if decisive else None
    return {
        "total_events": len(records),
        "effective_control_events": same_valid,
        "same_collision_excluded": same_collision,
        "same_success_events": same_success,
        "same_failure_events": same_fail,
        "eligible_identity_events": eligible_events,
        "effective_interference_trials": similar_valid,
        "similar_collision_excluded": similar_collision,
        "uncertain_trials": uncertain,
        "decidable_trials": decisive,
        "retain_trials": retain,
        "switch_trials": switch,
        "rfr_pct": pct(ofr),
        "dsr_pct": pct(cier),
        "trial_dsr_pct": pct(trial_cier),
    }


def _ic_behavior_event_metrics(records: list[dict[str, Any]], version: str) -> dict[str, Any]:
    """Aggregate the current Same-referenced binary behavioral labels.

    This branch is deliberately separate from the legacy OTPR branch. A
    result file must carry the explicit evaluator version before these labels
    are interpreted as current IC results.
    """
    same_valid = same_fail = same_success = 0
    similar_valid = similar_follow_original = similar_failure = 0
    eligible_events = 0
    event_rates: list[float] = []
    for record in records:
        data = record["data"]
        if data.get("identity_evaluator_version") != version:
            continue
        if data.get("same_success") is not True:
            same_valid += 1
            same_fail += 1
            continue
        same_valid += 1
        same_success += 1
        trials = data.get("similar_results") or data.get("identity_trial_results") or []
        event_total = event_positive = 0
        for trial in trials:
            label = trial.get("behavior_label") if isinstance(trial, dict) else None
            if label not in {"follow_original_target", "failure"}:
                continue
            event_total += 1
            similar_valid += 1
            if label == "follow_original_target":
                event_positive += 1
                similar_follow_original += 1
            else:
                similar_failure += 1
        if event_total:
            eligible_events += 1
            event_rates.append(event_positive / event_total)
    return {
        "protocol_version": version,
        "total_events": len(records),
        "effective_control_events": same_valid,
        "same_collision_excluded": 0,
        "same_success_events": same_success,
        "same_failure_events": same_fail,
        "eligible_identity_events": eligible_events,
        "effective_interference_trials": similar_valid,
        "similar_follow_original_trials": similar_follow_original,
        "similar_failure_trials": similar_failure,
        "effective_follow_ratio_pct": pct(mean(event_rates)) if event_rates else None,
        "rfr_pct": pct(same_fail / same_valid) if same_valid else None,
        "dsr_pct": None,
        "trial_dsr_pct": None,
        "otpr_used_for_decision": False,
    }


def summarize_ic(records: list[dict[str, Any]], reps: int, seed: int) -> dict[str, Any]:
    result = ic_event_metrics(records)
    if reps > 0 and records:
        def ofr(rows: list[dict[str, Any]]) -> float | None:
            return ic_event_metrics(rows)["rfr_pct"]
        def cier(rows: list[dict[str, Any]]) -> float | None:
            return ic_event_metrics(rows)["dsr_pct"]
        result["rfr_ci95_low"], result["rfr_ci95_high"] = bootstrap_scalar(records, ofr, reps, seed)
        result["dsr_ci95_low"], result["dsr_ci95_high"] = bootstrap_scalar(records, cier, reps, seed + 1)
        if result.get("protocol_version") == "eovt-ic-behavior-v0.1":
            def follow_ratio(rows: list[dict[str, Any]]) -> float | None:
                value = ic_event_metrics(rows).get("effective_follow_ratio_pct")
                return as_float(value)
            result["effective_follow_ratio_ci95_low"], result["effective_follow_ratio_ci95_high"] = bootstrap_scalar(
                records, follow_ratio, reps, seed + 2
            )
    else:
        result["rfr_ci95_low"] = result["rfr_ci95_high"] = None
        result["dsr_ci95_low"] = result["dsr_ci95_high"] = None
        if result.get("protocol_version") == "eovt-ic-behavior-v0.1":
            result["effective_follow_ratio_ci95_low"] = None
            result["effective_follow_ratio_ci95_high"] = None
    return result

