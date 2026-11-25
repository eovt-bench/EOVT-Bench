"""Initial IC behavioral scorer.

IC is scored from the complete Same-referenced robot trajectory and pose
evidence. OTPR is intentionally not used for the binary decision. A Similar
trial is positive only when it preserves the original-target following
behavior under the frozen initial thresholds.

The input is an event object with:
  {"same": {"records": [...]}, "similar": [{"records": [...]}, ...]}

Each record contains robot_position, robot_heading, original_position and,
for Similar trials, distractor_position. Positions can be 2-D or 3-D.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


VERSION = "eovt-ic-behavior-v0.1"


def _position(row: dict[str, Any], key: str) -> np.ndarray:
    value = row.get(key)
    if value is None:
        aliases = {
            "robot_position": ("robot_pos", "robot_base_position"),
            "original_position": ("target_position", "target_pos"),
            "distractor_position": ("candidate_position", "similar_position"),
        }
        for alias in aliases.get(key, ()):
            if row.get(alias) is not None:
                value = row[alias]
                break
    if value is None:
        raise ValueError(f"Missing IC position field: {key}")
    array = np.asarray(value, dtype=float).reshape(-1)
    if array.size < 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"Invalid IC position field: {key}")
    return array[:3] if array.size >= 3 else np.asarray([array[0], 0.0, array[1]])


def _heading(row: dict[str, Any]) -> float:
    for key in ("robot_heading_rad", "heading_rad", "robot_yaw_rad"):
        if row.get(key) is not None:
            value = float(row[key])
            if math.isfinite(value):
                return value
    for key in ("robot_heading_deg", "heading_deg", "robot_yaw_deg"):
        if row.get(key) is not None:
            value = math.radians(float(row[key]))
            if math.isfinite(value):
                return value
    raise ValueError("Missing IC robot heading")


def _xz(values: list[np.ndarray]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[:, [0, 2]]


def _path_length(path: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum()) if len(path) > 1 else 0.0


def _dtw_rms(a: np.ndarray, b: np.ndarray) -> float:
    m, n = len(a), len(b)
    cost = np.full((m + 1, n + 1), np.inf, dtype=float)
    cost[0, 0] = 0.0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            distance = float(np.linalg.norm(a[i - 1] - b[j - 1]))
            cost[i, j] = distance * distance + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    return float(math.sqrt(cost[m, n] / max(1, m + n)))


def _discrete_frechet(a: np.ndarray, b: np.ndarray) -> float:
    cache = np.full((len(a), len(b)), -1.0, dtype=float)

    def rec(i: int, j: int) -> float:
        if cache[i, j] >= 0:
            return float(cache[i, j])
        distance = float(np.linalg.norm(a[i] - b[j]))
        if i == 0 and j == 0:
            value = distance
        elif i == 0:
            value = max(rec(0, j - 1), distance)
        elif j == 0:
            value = max(rec(i - 1, 0), distance)
        else:
            value = max(min(rec(i - 1, j), rec(i - 1, j - 1), rec(i, j - 1)), distance)
        cache[i, j] = value
        return value

    return rec(len(a) - 1, len(b) - 1)


def _angle_error(robot: np.ndarray, heading: float, person: np.ndarray) -> float:
    forward = np.asarray([math.cos(heading), math.sin(heading)], dtype=float)
    vector = (person - robot)[[0, 2]]
    norm = float(np.linalg.norm(vector))
    if norm < 1e-8:
        return 180.0
    cosine = float(np.clip(np.dot(forward, vector / norm), -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def _resample(values: list[float], count: int) -> np.ndarray:
    if not values:
        raise ValueError("Cannot resample an empty sequence")
    if len(values) == count:
        return np.asarray(values, dtype=float)
    source = np.linspace(0.0, 1.0, len(values))
    target = np.linspace(0.0, 1.0, count)
    return np.interp(target, source, np.asarray(values, dtype=float))


def _wrapped_heading_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.abs((a - b + np.pi) % (2 * np.pi) - np.pi)


def _trial_records(trial: dict[str, Any]) -> list[dict[str, Any]]:
    records = trial.get("records") or trial.get("trajectory") or trial.get("steps")
    if not isinstance(records, list) or len(records) < 2:
        raise ValueError("IC trial requires at least two trajectory records")
    return [row for row in records if isinstance(row, dict)]


def _trajectory_metrics(same_rows: list[dict[str, Any]], similar_rows: list[dict[str, Any]]) -> dict[str, float | bool]:
    same_robot = _xz([_position(row, "robot_position") for row in same_rows])
    similar_robot = _xz([_position(row, "robot_position") for row in similar_rows])
    same_target = _xz([_position(row, "original_position") for row in same_rows])
    similar_target = _xz([_position(row, "original_position") for row in similar_rows])
    dtw = _dtw_rms(same_robot, similar_robot)
    frechet = _discrete_frechet(same_robot, similar_robot)
    endpoint = float(np.linalg.norm(same_robot[-1] - similar_robot[-1]))
    same_length = _path_length(same_robot)
    similar_length = _path_length(similar_robot)
    length_diff = abs(same_length - similar_length)
    length_limit = max(0.5, 0.35 * same_length)
    target_dtw = _dtw_rms(same_target, similar_target)
    target_frechet = _discrete_frechet(same_target, similar_target)
    target_length_diff = abs(_path_length(same_target) - _path_length(similar_target))
    same_heading = _resample([_heading(row) for row in same_rows], max(2, min(len(same_rows), len(similar_rows))))
    similar_heading = _resample([_heading(row) for row in similar_rows], len(same_heading))
    heading_difference = np.degrees(_wrapped_heading_difference(same_heading, similar_heading))
    split = max(1, len(heading_difference) // 2)
    heading_fraction_first = float(np.mean(heading_difference[:split] <= 45.0))
    heading_fraction_second = float(np.mean(heading_difference[split:] <= 45.0))
    return {
        "robot_dtw_rms_m": dtw,
        "robot_discrete_frechet_m": frechet,
        "robot_endpoint_error_m": endpoint,
        "robot_length_difference_m": length_diff,
        "robot_length_allowance_m": length_limit,
        "target_dtw_rms_m": target_dtw,
        "target_discrete_frechet_m": target_frechet,
        "target_length_difference_m": target_length_diff,
        "body_heading_difference_mean_deg": float(np.mean(heading_difference)),
        "body_heading_fraction_first": heading_fraction_first,
        "body_heading_fraction_second": heading_fraction_second,
        "target_motion_altered": bool(
            target_dtw > 0.75
            or target_frechet > 1.5
            or target_length_diff > max(0.5, 0.35 * _path_length(same_target))
        ),
    }


def score_similar_trial(same_trial: dict[str, Any], similar_trial: dict[str, Any]) -> dict[str, Any]:
    same_rows = _trial_records(same_trial)
    similar_rows = _trial_records(similar_trial)
    metrics = _trajectory_metrics(same_rows, similar_rows)
    trajectory_agrees = (
        metrics["robot_dtw_rms_m"] <= 0.75
        and metrics["robot_discrete_frechet_m"] <= 1.5
        and metrics["robot_endpoint_error_m"] <= 1.0
        and metrics["robot_length_difference_m"] <= metrics["robot_length_allowance_m"]
        and metrics["body_heading_fraction_first"] >= 0.8
        and metrics["body_heading_fraction_second"] >= 0.8
    )
    original_support = []
    distractor_support = []
    distractor_advantage = []
    timestamps = []
    for row in similar_rows:
        timestamp = row.get("simulation_time_s", row.get("time_s"))
        if timestamp is None:
            timestamps.append(float(len(timestamps)))
        else:
            timestamps.append(float(timestamp))
        robot = _position(row, "robot_position")
        original = _position(row, "original_position")
        heading = _heading(row)
        original_distance = float(np.linalg.norm(robot - original))
        original_angle = _angle_error(robot, heading, original)
        original_ok = 0.5 <= original_distance <= 3.0 and original_angle <= 45.0
        original_support.append(original_ok)
        if row.get("distractor_position") is not None or row.get("candidate_position") is not None:
            distractor = _position(row, "distractor_position")
            distractor_distance = float(np.linalg.norm(robot - distractor))
            distractor_angle = _angle_error(robot, heading, distractor)
            angular_advantage = original_angle - distractor_angle
            distractor_advantage.append(
                distractor_distance <= 3.0
                and distractor_angle <= 45.0
                and angular_advantage >= 15.0
                and abs(original_angle - distractor_angle) >= 25.0
            )
    end_time = timestamps[-1]
    terminal_indices = [index for index, timestamp in enumerate(timestamps) if timestamp >= end_time - 1.0]
    if not terminal_indices:
        terminal_indices = [len(original_support) - 1]
    terminal_support = sum(original_support[index] for index in terminal_indices) / len(terminal_indices)
    clear_distractor = bool(
        distractor_advantage
        and sum(distractor_advantage[index] for index in terminal_indices if index < len(distractor_advantage))
        / max(1, sum(index < len(distractor_advantage) for index in terminal_indices))
        >= 0.6
    )
    label = "failure"
    reason = "unmet_original_following_criterion"
    if str(similar_trial.get("status", "")).lower() in {"lost", "collision"} or similar_trial.get("collision"):
        reason = "lost_or_collision"
    elif clear_distractor:
        reason = "stable_terminal_distractor_preference"
    elif trajectory_agrees and not metrics["target_motion_altered"]:
        label = "follow_original_target"
        reason = "same_referenced_robot_path_agreement"
    elif terminal_support >= 0.6 and sum(original_support) / len(original_support) >= 0.6:
        label = "follow_original_target"
        reason = "stable_original_pose_support"
    return {
        "identity_evaluator_version": VERSION,
        "behavior_label": label,
        "failure_reason": None if label == "follow_original_target" else reason,
        **metrics,
        "trajectory_agrees_with_same": bool(trajectory_agrees),
        "whole_trial_original_support_fraction": sum(original_support) / len(original_support),
        "terminal_original_support_fraction": terminal_support,
        "terminal_distractor_preference": clear_distractor,
    }


def score_event(event: dict[str, Any]) -> dict[str, Any]:
    same_trial = event.get("same")
    similar_trials = event.get("similar") or event.get("similar_trials")
    if not isinstance(same_trial, dict) or not isinstance(similar_trials, list) or len(similar_trials) != 3:
        raise ValueError("IC event requires one Same and three Similar trials")
    same_rows = _trial_records(same_trial)
    same_success = bool(same_trial.get("success", 1.0)) and not bool(same_trial.get("collision", False))
    if not same_success:
        return {
            "identity_evaluator_version": VERSION,
            "same_success": False,
            "similar_results": [],
            "similar_follow_original_count": 0,
            "effective_follow_ratio": None,
            "event_label": "same_control_failure",
        }
    results = [score_similar_trial(same_trial, trial) for trial in similar_trials]
    retained = sum(row["behavior_label"] == "follow_original_target" for row in results)
    return {
        "identity_evaluator_version": VERSION,
        "same_success": True,
        "same_record_count": len(same_rows),
        "similar_results": results,
        "similar_count": len(results),
        "similar_follow_original_count": retained,
        "effective_follow_ratio": retained / len(results),
        "event_label": "evaluated",
    }
