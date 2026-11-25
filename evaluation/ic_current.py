"""Same-qualified IC scoring, matching the frozen November 23 v0.7 audit."""
from __future__ import annotations
import math
from typing import Any
import numpy as np
import ic_rules as rules
import ic_spatial as spatial
from ic_same import assess as assess_same

VERSION = "eovt-ic-behavior-v0.2"


class SpatialWorker:
    """Weighted full-boundary DTW and discrete Frechet; deterministic ties."""
    def compare(self, a, b, eps=1.5):
        a, b = np.asarray(a), np.asarray(b)
        m, n = len(a), len(b)
        if not m or not n:
            raise ValueError("Empty spatial curve")
        pointer = np.zeros((m+1, n+1), dtype=np.uint8)
        cost, frechet = np.full(n+1, np.inf), np.full(n+1, np.inf)
        repeats = np.zeros(n+1, dtype=int)
        cost[0] = frechet[0] = 0.0
        for i in range(1, m+1):
            nc, nf, nr = np.full(n+1, np.inf), np.full(n+1, np.inf), np.zeros(n+1, dtype=int)
            distances = np.sum((a[i-1]-b)**2, axis=1)
            for j in range(1, n+1):
                c = float(distances[j-1])
                best, rep, direction = cost[j-1]+2*c, repeats[j-1], 1
                for value, repeat, direct in ((cost[j]+c, repeats[j]+1, 2),
                                               (nc[j-1]+c, nr[j-1]+1, 3)):
                    if value < best or (value == best and repeat < rep):
                        best, rep, direction = value, repeat, direct
                nc[j], nr[j], pointer[i, j] = best, rep, direction
                nf[j] = max(math.sqrt(c), min(frechet[j-1], frechet[j], nf[j-1]))
            cost, repeats, frechet = nc, nr, nf
        path = []
        i, j = m, n
        while i and j:
            path.append([i-1, j-1])
            direction = pointer[i, j]
            i -= int(direction in (1, 2))
            j -= int(direction in (1, 3))
        if i or j:
            raise ValueError("Incomplete DTW boundary")
        return dict(dtw_rms=math.sqrt(cost[n]/(m+n)), frechet=float(frechet[n]),
                    path=path[::-1], size_a=m, size_b=n)


def _records(trial):
    rows = trial.get("records", trial.get("trajectory"))
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("Complete IC trajectory required")
    result = []
    for row in rows:
        timestamp = row.get("simulation_time_s")
        if timestamp is None or not math.isfinite(float(timestamp)):
            raise ValueError("Actual simulation_time_s is required; presentation time is invalid")
        if "robot" in row and "target" in row:
            normalized = dict(row)
        else:
            if "robot_heading_rad" not in row:
                raise ValueError("Missing robot heading")
            heading = float(row["robot_heading_rad"])
            robot = dict(position=row["robot_position"],
                         forward=[math.cos(heading), 0., math.sin(heading)],
                         rotation_matrix_rows=np.eye(3).tolist())
            target = dict(position=row["original_position"], forward=[1., 0., 0.],
                          rotation_matrix_rows=np.eye(3).tolist())
            candidate = (dict(position=row["distractor_position"], forward=[1., 0., 0.])
                         if row.get("distractor_position") is not None else None)
            normalized = dict(row, robot=robot, target=target, candidate=candidate,
                              candidate_active=bool(row.get("candidate_active", candidate is not None)))
        normalized["simulation_time_s"] = float(timestamp)
        result.append(normalized)
    rules.validate(result, "trial")
    if any(b["simulation_time_s"]-a["simulation_time_s"] > 0.2+1e-9
           for a, b in zip(result, result[1:])):
        raise ValueError("IC evidence gap exceeds 0.2 seconds")
    return result


def qualify_same(same_trial):
    rows = _records(same_trial)
    status = same_trial.get("status")
    end_reason = same_trial.get("end_reason")
    if end_reason is None:
        end_reason = ("episode_over" if status == "Normal" and same_trial.get("finish") is True
                      else status)
    if end_reason is None:
        raise ValueError("Same termination evidence is required")
    info = dict(end_reason=end_reason, end_reason_source="same_run_result",
                original_same_success=same_trial.get("success", ""),
                same_success_evidence="same_run_result" if "success" in same_trial else "missing")
    result = assess_same(rows, info)
    if same_trial.get("collision"):
        result["same_success_geometry"] = False
        result["same_geometry_label"] = "失败"
        result["checks"]["no_recorded_collision"] = False
        result["failed_checks"].append("no_recorded_collision")
        result["reason"] = "同次运行记录存在碰撞；Same不满足资格。"
    result["qualification_version"] = VERSION
    return result


def score_similar_trial(same_trial, similar_trial, *, require_qualified_same=True):
    same, similar = _records(same_trial), _records(similar_trial)
    qualification = qualify_same(same_trial)
    if require_qualified_same and not qualification["same_success_geometry"]:
        raise ValueError("Unqualified Same: exclude the pair from the IC denominator")
    active = next((i for i, row in enumerate(similar) if row.get("candidate_active")), None)
    if active is None:
        raise ValueError("Similar trial has no recorded activation")
    active_rows = similar[active:]
    if len(active_rows) < 2 or not all(row.get("candidate_active") for row in active_rows):
        raise ValueError("Incomplete post-activation evidence")
    same_rows = spatial.crop_same(same, active_rows[0]["simulation_time_s"])
    if len(same_rows) < 2:
        raise ValueError("Same does not cover the activation boundary")
    metrics, pose = rules.measurements(spatial, SpatialWorker(), same_rows, active_rows)
    frames = [rules.direct_frame(row) for row in active_rows]
    start, end = frames[0]["simulation_time_s"], frames[-1]["simulation_time_s"]
    whole = rules.time_stats(frames, start, end)
    terminal = rules.time_stats(frames, max(start, end-1.0), end)
    minimum = min(math.dist(row["robot"]["position"], row["target"]["position"])
                  for row in similar[1:])
    end_reason = similar_trial.get("end_reason", similar_trial.get("status"))
    if end_reason is None:
        raise ValueError("Similar termination evidence is required")
    if similar_trial.get("collision"):
        end_reason = "Collision"
    judged = rules.decision(metrics, pose, whole, terminal, end_reason, minimum < 0.5)
    retained = judged["final_label"] == "跟随原目标"
    return dict(identity_evaluator_version=VERSION, protocol_version="eovt-or-ic-v0.2",
                behavior_label="follow_original_target" if retained else "failure",
                failure_reason=None if retained else judged["code"],
                same_qualification=qualification, metrics=metrics, pose=pose,
                whole=whole, terminal=terminal, first_activation_time_s=start,
                last_frame=frames[-1], otpr_used_for_decision=False, **judged)


def score_event(event: dict[str, Any]):
    same = event.get("same")
    similar = event.get("similar", event.get("similar_trials"))
    if not isinstance(same, dict) or not isinstance(similar, list) or len(similar) != 3:
        raise ValueError("IC requires one Same and three distinct Similar trials")
    identities=[trial.get("actor_name",trial.get("candidate_id")) for trial in similar]
    if any(identity is None for identity in identities) or len(set(identities)) != 3:
        raise ValueError("IC requires three recorded, distinct Similar person IDs")
    qualification = qualify_same(same)
    if not qualification["same_success_geometry"]:
        return dict(identity_evaluator_version=VERSION, same_success=False,
                    same_valid_geometry=False, same_qualification=qualification,
                    similar_count=0, similar_follow_original_count=0,
                    similar_results=[], effective_follow_ratio=None,
                    event_label="same_control_failure")
    results = [score_similar_trial(same, trial) for trial in similar]
    retained = sum(row["behavior_label"] == "follow_original_target" for row in results)
    return dict(identity_evaluator_version=VERSION, same_success=True,
                same_valid_geometry=True, same_qualification=qualification,
                original_same_success=same.get("success"),
                similar_count=3, similar_follow_original_count=retained,
                similar_results=results, effective_follow_ratio=retained/3,
                event_label="evaluated")
