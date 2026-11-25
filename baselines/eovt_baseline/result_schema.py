from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from .paths import writable_path


REQUIRED_FINAL = ("success", "following_rate", "collision")


def _json_default(value: Any) -> Any:
    """Convert NumPy/Magnum/path values emitted by Habitat to JSON safely."""
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except (ValueError, TypeError):
            pass
    try:
        return list(value)
    except TypeError:
        return repr(value)


def valid_final_result(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.name.endswith("_info.json") or not candidate.is_file():
        return False
    try:
        with candidate.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return False
        return all(
            isinstance(data.get(key), (int, float))
            and not isinstance(data[key], bool)
            and math.isfinite(float(data[key]))
            and 0 <= float(data[key]) <= 1
            for key in REQUIRED_FINAL
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = writable_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + f".{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False, default=_json_default)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(destination)
    return destination


def validate_result(data: dict[str, Any], task: str | None = None) -> list[str]:
    errors = []
    for key in REQUIRED_FINAL:
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            errors.append(f"missing/non-finite {key}")
        elif not 0.0 <= float(value) <= 1.0:
            errors.append(f"{key} outside [0,1]")
    selected = (task or str(data.get("task", ""))).lower()
    if selected == "or":
        for key, alias in (("rsr", "reacquisition_success"), ("vor", "visibility_opportunity")):
            value = data.get(key, data.get(alias))
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                errors.append(f"missing/non-finite {key}")
            elif not 0 <= value <= 1:
                errors.append(f"{key} outside [0,1]")
    if selected == "ic":
        trials = data.get("identity_trial_results")
        if not isinstance(trials, list) or len(trials) != 4 or any(not isinstance(t, dict) for t in trials):
            errors.append("IC requires four identity_trial_results")
        elif (
            sum(t.get("condition") == "same" for t in trials) != 1
            or sum(t.get("condition") in ("similar", "swap", "similar_swap") for t in trials) != 3
        ):
            errors.append("IC requires one Same and three Similar trials")
        else:
            for index, trial in enumerate(trials):
                for key in ("success", "collision"):
                    value = trial.get(key)
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                        errors.append(f"trial {index}: missing/non-finite {key}")
                    elif not 0 <= value <= 1:
                        errors.append(f"trial {index}: {key} outside [0,1]")
    return errors

