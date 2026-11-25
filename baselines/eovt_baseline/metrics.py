from __future__ import annotations

import math
from statistics import median
from typing import Any, Iterable


def generic_metrics(step_records: list[dict[str, Any]], final_info: dict[str, Any], max_steps: int) -> dict[str, float]:
    if not step_records:
        return {"success": 0.0, "following_rate": 0.0, "collision": 0.0}
    following = [float(record.get("human_following", 0.0)) for record in step_records]
    collision = float(bool(final_info.get("human_collision", final_info.get("collision", False))))
    if len(step_records) < max_steps:
        success = float(bool(final_info.get("human_following_success", False)) and bool(following[-1]))
    else:
        success = float(bool(following[-1]))
    return {
        "success": success,
        "following_rate": sum(following) / len(following),
        "collision": collision,
    }


def occlusion_metrics(visibility: Iterable[bool]) -> dict[str, float | int | None]:
    """Compatibility implementation of the current EOVT-Bench OR protocol.

    A loss event begins at the first visible->not-visible transition. VOR means
    a post-loss observation window exists; RSR means visibility later returns;
    CRR is RSR conditional on that opportunity. K=1.
    """
    trace = [bool(value) for value in visibility]
    lost_index = next((i for i in range(1, len(trace)) if trace[i - 1] and not trace[i]), None)
    opportunity = lost_index is not None and lost_index + 1 < len(trace)
    reacquired_index = None
    if lost_index is not None:
        reacquired_index = next((i for i in range(lost_index + 1, len(trace)) if trace[i]), None)
    reacquired = reacquired_index is not None
    rsr = float(reacquired)
    vor = float(opportunity)
    crr = float(reacquired) if opportunity else 0.0
    return {
        "visibility_opportunity": float(opportunity),
        "reacquisition_success": rsr,
        "conditional_reacquisition": crr,
        "rsr": rsr,
        "vor": vor,
        "crr": crr,
        "recovery_steps": (reacquired_index - lost_index) if reacquired else None,
        "lost_index": lost_index,
        "reacquired_index": reacquired_index,
        "protocol_k": 1,
    }


def identity_metrics(trials: list[dict[str, Any]]) -> dict[str, float | int]:
    same = [float(t["success"]) for t in trials if t.get("condition") == "same"]
    similar = [
        float(t["target_retained"])
        for t in trials
        if t.get("condition") in {"similar", "swap", "similar_swap"} and t.get("target_retained") is not None
    ]
    same_sr = sum(same) / len(same) if same else 0.0
    similar_sr = sum(similar) / len(similar) if similar else 0.0
    bia = (same_sr + similar_sr) / 2.0
    return {
        "same_success_rate": same_sr,
        "similar_success_rate": similar_sr,
        # Legacy aliases are retained only so older result readers remain usable.
        "swap_success_rate": similar_sr,
        "similar_swap_success": similar_sr,
        "balanced_identity_accuracy": bia,
        "same_sr": same_sr,
        "similar_sr": similar_sr,
        "swap_sr": similar_sr,
        "bia": bia,
        "same_trials": len(same),
        "similar_trials": len(similar),
        "swap_trials": len(similar),
    }


def mean_metric(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float)) and math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else None


def median_metric(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float)) and math.isfinite(float(row[key]))]
    return median(values) if values else None

