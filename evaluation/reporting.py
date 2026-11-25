"""Public reporting API: preserve metric eligibility and expose data issues."""
from __future__ import annotations

import json
from pathlib import Path

from shared_analysis import as_float, load_json_records, summarize_ic, summarize_or, summarize_stt

VERSION = "eovt-evaluator-20261125"
SUMMARIZERS = {"stt": summarize_stt, "or": summarize_or, "ic": summarize_ic}


def summarize_directory(path: Path, task: str, repetitions: int = 2000, seed: int = 20261121) -> dict:
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
                or sum(t.get("condition") in ("swap", "similar_swap") for t in trials) != 3
            ):
                problems.append("incomplete or legacy IC structure")
        if problems:
            issues.append({"file": record["path"].name, "issues": problems})
    summary = SUMMARIZERS[task](records, repetitions, seed)
    return {
        "evaluator_version": VERSION,
        "task": task,
        "parsed_final_records": len(records),
        "bootstrap_unit": "layout",
        "bootstrap_repetitions": repetitions,
        "seed": seed,
        "unreadable_records": errors,
        "field_issues": issues,
        "summary": summary,
    }
