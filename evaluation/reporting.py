"""Public reporting API: preserve metric eligibility and expose data issues."""
from __future__ import annotations

import json
from pathlib import Path

from shared_analysis import (
    as_float, has_layout_evidence, layout_id, load_json_records,
    summarize_ic, summarize_or, summarize_stt,
)

VERSION = "eovt-evaluator-20261125-v0.2"
SUMMARIZERS = {"stt": summarize_stt, "or": summarize_or, "ic": summarize_ic}


def summarize_directory(
    path: Path, task: str, repetitions: int = 2000, seed: int = 20261121,
    *, allow_legacy: bool = False,
) -> dict:
    if not path.is_dir():
        raise FileNotFoundError(f"result directory does not exist: {path}")
    records, errors = load_json_records(path)
    issues = []
    seen = set()
    for record in records:
        data = record["data"]
        event_id = data.get("episode_id") or record["path"].stem
        if event_id in seen:
            raise ValueError(f"duplicate final event ID: {event_id}")
        seen.add(event_id)
        problems = []
        current_ic = data.get("identity_evaluator_version") == "eovt-ic-behavior-v0.2"
        current_or = data.get("protocol_version") == "eovt-or-visibility-v0.2"
        if task in {"or", "ic"} and not (current_ic if task == "ic" else current_or) and not allow_legacy:
            raise ValueError(
                f"{record['path'].name}: current {task.upper()} scorer version is required; "
                "historical analysis requires explicit --allow-legacy"
            )
        if repetitions > 0 and not has_layout_evidence(record):
            raise ValueError(
                f"{record['path'].name}: missing layout/layout_id; "
                "an arbitrary event ID cannot be used as a bootstrap cluster"
            )
        if (task == "ic" and current_ic) or (task == "or" and current_or):
            if current_ic:
                trials = data.get("similar_results")
                if not isinstance(data.get("same_success"), bool):
                    problems.append("missing boolean Same eligibility")
                if data.get("same_success") is True and (
                    not isinstance(trials,list) or len(trials)!=3 or
                    any(not isinstance(t, dict) or t.get("behavior_label") not in
                        {"follow_original_target","failure"} for t in trials)
                ):
                    problems.append("current eligible IC requires three binary Similar labels")
            else:
                for field in ("actual_loss","opportunity","recovered","censored"):
                    if not isinstance(data.get(field),bool):
                        problems.append("missing boolean "+field)
            if problems:
                raise ValueError(f"{record['path'].name}: {problems}")
            continue
        for field in ("success", "following_rate", "collision"):
            value = as_float(data.get(field))
            if value is None:
                problems.append(f"missing/non-finite/non-numeric {field}")
            elif not 0 <= value <= 1:
                raise ValueError(f"{record['path'].name}: {field} outside [0,1]")
        if task == "or":
            for field in ("rsr", "vor"):
                alias = "reacquisition_success" if field == "rsr" else "visibility_opportunity"
                if field not in data and alias in data:
                    data[field] = data[alias]
                value = as_float(data.get(field))
                if value is None:
                    problems.append(f"missing/non-finite {field}")
                elif not 0 <= value <= 1:
                    raise ValueError(f"{record['path'].name}: {field} outside [0,1]")
        if task == "ic":
            trials = data.get("identity_trial_results") or []
            if not isinstance(trials, list) or any(not isinstance(t, dict) for t in trials):
                raise ValueError(f"{record['path'].name}: trials must be a list of objects")
            if (
                len(trials) != 4
                or sum(t.get("condition") == "same" for t in trials) != 1
                or sum(t.get("condition") in ("similar", "swap", "similar_swap") for t in trials) != 3
            ):
                problems.append("incomplete or legacy IC structure")
        if problems:
            issues.append({"file": record["path"].name, "issues": problems})
    summary = SUMMARIZERS[task](records, repetitions, seed)
    source_versions = sorted({
        str(r["data"].get("identity_evaluator_version") or r["data"].get("online_summary_protocol")
            or "historical-unversioned")
        if task == "ic" else
        str(r["data"].get("protocol_version") or r["data"].get("online_summary_protocol")
            or ("existing-stt" if task == "stt" else "historical-unversioned"))
        for r in records
    })
    return {
        "evaluator_version": VERSION,
        "task": task,
        "parsed_final_records": len(records),
        "bootstrap_unit": "layout",
        "bootstrap_repetitions": repetitions,
        "seed": seed,
        "input_protocol_versions": source_versions,
        "legacy_analysis_explicitly_allowed": allow_legacy,
        "layout_count": len({layout_id(r) for r in records if has_layout_evidence(r)}),
        "unreadable_records": errors,
        "field_issues": issues,
        "summary": summary,
    }
