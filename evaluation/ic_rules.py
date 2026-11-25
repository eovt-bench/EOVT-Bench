"""Frozen full-path geometry and elapsed-time IC rules. No model code."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import numpy as np
EPS = 1e-9
CONFIG_ROOT = Path(__file__).resolve().parents[1] / "configs/evaluation"
CONFIG = json.loads((CONFIG_ROOT / "ic_behavior_v0.2.json").read_text())

def angle(forward, person_delta):
    fx, fz = forward[0], forward[2]
    dx, dz = person_delta[0], person_delta[2]
    denominator = math.hypot(fx, fz) * math.hypot(dx, dz)
    if denominator <= 1e-12:
        return None
    cosine = max(-1.0, min(1.0, (fx * dx + fz * dz) / denominator))
    return math.degrees(math.acos(cosine))

def delta(a, b):
    return [x - y for x, y in zip(a, b)]

def direct_frame(row):
    cfg = CONFIG["direct_geometry"]
    robot, target, distractor = row["robot"], row["target"], row["candidate"]
    vt = delta(target["position"], robot["position"])
    vd = delta(distractor["position"], robot["position"])
    dt, dd = math.sqrt(sum(x*x for x in vt)), math.sqrt(sum(x*x for x in vd))
    at, ad = angle(robot["forward"], vt), angle(robot["forward"], vd)
    separation = angle(vt, vd)
    in_range = cfg["following_distance_lower_m_inclusive"] - EPS <= dt <= cfg["following_distance_upper_m_inclusive"] + EPS
    d_in_range = cfg["following_distance_lower_m_inclusive"] - EPS <= dd <= cfg["following_distance_upper_m_inclusive"] + EPS
    d_clear = (
        at is not None and ad is not None and separation is not None
        and d_in_range
        and ad <= cfg["distractor_heading_limit_deg"] + EPS
        and at - ad >= cfg["clear_distractor_angular_advantage_deg"] - EPS
        and separation >= cfg["clear_distractor_bearing_separation_deg"] - EPS
    )
    return dict(
        step=row["step"], simulation_time_s=row["simulation_time_s"],
        original_distance_m=dt, distractor_distance_m=dd,
        original_angle_deg=at, distractor_angle_deg=ad,
        person_bearing_separation_deg=separation,
        original_in_range=in_range,
        original_within_angle=at is not None and at <= cfg["original_heading_limit_deg"] + EPS,
        original_support=bool(in_range and at is not None and at <= cfg["original_heading_limit_deg"] + EPS and not d_clear),
        clear_distractor_support=bool(d_clear),
    )

def time_stats(frames, start, end):
    duration = end - start
    keys = ("original_support", "clear_distractor_support",
            "original_in_range", "original_within_angle")
    totals, runs, longest = ({key: 0.0 for key in keys} for _ in range(3))
    angle_sum = distance_sum = covered = 0.0
    for previous, current in zip(frames, frames[1:]):
        left = max(start, previous["simulation_time_s"])
        right = min(end, current["simulation_time_s"])
        dt = max(0.0, right-left)
        if dt <= 0:
            continue
        valid_gap = current["simulation_time_s"] - previous["simulation_time_s"] <= CONFIG["temporal"]["maximum_evidence_gap_s"] + EPS
        if not valid_gap:
            for key in keys:
                runs[key] = 0.0
            continue
        covered += dt
        angle_sum += dt * (current["original_angle_deg"] if current["original_angle_deg"] is not None else 180.0)
        distance_sum += dt * current["original_distance_m"]
        for key in keys:
            if current[key]:
                totals[key] += dt
                runs[key] += dt
                longest[key] = max(longest[key], runs[key])
            else:
                runs[key] = 0.0
    result = dict(duration_s=duration, covered_s=covered,
                  time_weighted_original_angle_deg=angle_sum/covered if covered else None,
                  time_weighted_original_distance_m=distance_sum/covered if covered else None)
    for key in keys:
        result[key+"_s"] = totals[key]
        result[key+"_fraction"] = totals[key]/duration if duration > EPS else 0.0
        result[key+"_longest_s"] = longest[key]
    result["last_frame_original_support"] = frames[-1]["original_support"]
    result["last_frame_distractor_support"] = frames[-1]["clear_distractor_support"]
    return result

def stable_terminal(stats, original):
    cfg = CONFIG["temporal"]
    key = "original_support" if original else "clear_distractor_support"
    last = "last_frame_original_support" if original else "last_frame_distractor_support"
    return (
        stats["duration_s"] >= cfg["terminal_duration_minimum_s"]-EPS
        and stats[key+"_fraction"] >= cfg["terminal_support_fraction_minimum"]-EPS
        and stats[key+"_longest_s"] >= cfg["terminal_continuous_support_minimum_s"]-EPS
        and stats[last]
    )

def decision(metrics, pose, whole, terminal, end_reason, collision_proxy):
    cfg = CONFIG["full_path"]
    allowance = max(cfg["length_difference_minimum_allowance_m"],
                    cfg["length_difference_same_fraction_allowance"] * metrics["path_length_same_m"])
    path_checks = dict(
        dtw=metrics["dtw_position_rms_m"] <= cfg["dtw_rms_limit_m"]+EPS,
        frechet=metrics["discrete_frechet_m"] <= cfg["frechet_limit_m"]+EPS,
        endpoint=metrics["endpoint_gap_m"] <= cfg["endpoint_limit_m"]+EPS,
        length=metrics["path_length_difference_m"] <= allowance+EPS,
        pose=min(pose["same_heading_fraction"], pose["similar_heading_fraction"]) >= cfg["heading_fraction_each_side_minimum"]-EPS,
    )
    ta = CONFIG["target_motion"]["altered_if_any"]
    length_m, length_fraction = ta["length_difference_above_maximum_of_m_and_same_fraction"]
    target_allowance = max(length_m, length_fraction * metrics["target_length_same_m"])
    target_difference = metrics["target_length_same_m"] - metrics["target_length_similar_m"]
    shortened = target_difference > target_allowance+EPS
    altered = (
        abs(target_difference) > target_allowance+EPS
        or metrics["target_dtw_position_rms_m"] > ta["dtw_rms_above_m"]+EPS
        or metrics["target_frechet_m"] > ta["frechet_above_m"]+EPS
    )
    terminal_t, terminal_d = stable_terminal(terminal, True), stable_terminal(terminal, False)
    whole_t = whole["original_support_fraction"] >= CONFIG["temporal"]["whole_original_support_fraction_minimum_for_pose_fallback"]-EPS
    full_path_pass = all(path_checks.values()) and not altered
    diagnostics = dict(
        target_motion_altered=altered, target_path_shortened=shortened,
        target_length_shortfall_m=target_difference, target_length_allowance_m=target_allowance,
        same_robot_path_applicable=not altered, full_robot_path_checks=path_checks,
        full_path_and_pose_pass=full_path_pass, stable_terminal_original=terminal_t,
        stable_terminal_distractor=terminal_d, whole_original_support_pass=whole_t,
        transient_reference_conflict_veto=False,
    )
    if collision_proxy:
        code, label, reason = "F_CONTACT_PROXY", "失败", "触发原目标与机器人距离小于0.5米的既有接近碰撞代理"
    elif end_reason == "Collision":
        code, label, reason = "F_COLLISION", "失败", "同次运行记录以Collision结束"
    elif end_reason == "Lost":
        code, label, reason = "F_LOST", "失败", "同次运行记录以Lost结束；不等同于确认跟随干扰者"
    elif terminal_d:
        code, label, reason = "F_DISTRACTOR_POSE", "失败", "末段持续朝向干扰者，且相对原目标具有明确角度优势"
    elif full_path_pass:
        code, label, reason = "T_FULL", "跟随原目标", "完整机器人轨迹及位姿与Same相符，末段无稳定干扰者偏好"
    elif terminal_t and whole_t:
        code, label = ("T_POSE_TARGET_ALTERED" if altered else "T_POSE"), "跟随原目标"
        reason = ("原目标运动改变，停用Same机器人路线门槛；全程及末段原目标距离与朝向条件成立"
                  if altered else "机器人路线存在偏差，但全程及末段原目标距离与朝向条件成立")
    else:
        code, label = "F_FOLLOW_CONDITION", "失败"
        if not terminal_t:
            reason = "末段未持续满足原目标跟随距离及朝向条件；未确认跟随干扰者"
        else:
            reason = "末段虽恢复朝向原目标，但全程原目标跟随条件不足且完整路线条件未通过"
    return dict(code=code, final_label=label, reason=reason,
                clear_distractor_behavior=code == "F_DISTRACTOR_POSE",
                diagnostics=diagnostics)

def validate(rows, role):
    if len(rows) < 2:
        raise ValueError(f"{role}: fewer than two observations")
    for a, b in zip(rows, rows[1:]):
        if b["simulation_time_s"] <= a["simulation_time_s"]:
            raise ValueError(f"{role}: non-increasing time")
    for row in rows:
        actors = ["robot", "target"] + (["candidate"] if row["candidate_active"] else [])
        for actor in actors:
            for key in ("position", "forward"):
                values = row[actor][key]
                if len(values) != 3 or not all(math.isfinite(x) for x in values):
                    raise ValueError(f"{role}: malformed {actor}.{key}")
        if math.hypot(row["robot"]["forward"][0], row["robot"]["forward"][2]) <= 1e-8:
            raise ValueError(f"{role}: undefined robot heading")

def measurements(module, worker, same, similar):
    a, b = module.arrays(same), module.arrays(similar)
    route = worker.compare(a["robot_curve"]["points"], b["robot_curve"]["points"])
    target = worker.compare(a["target_curve"]["points"], b["target_curve"]["points"])
    pose = module.pose_summary(a, b, module.correspondences(a, b, route))
    metrics = dict(
        dtw_position_rms_m=route["dtw_rms"], discrete_frechet_m=route["frechet"],
        path_length_same_m=float(a["robot_curve"]["arc"][-1]),
        path_length_similar_m=float(b["robot_curve"]["arc"][-1]),
        endpoint_gap_m=float(module.np.linalg.norm(a["p"][-1]-b["p"][-1])),
        target_length_same_m=float(a["target_curve"]["arc"][-1]),
        target_length_similar_m=float(b["target_curve"]["arc"][-1]),
        target_dtw_position_rms_m=target["dtw_rms"], target_frechet_m=target["frechet"],
    )
    metrics["path_length_difference_m"] = abs(metrics["path_length_same_m"]-metrics["path_length_similar_m"])
    return metrics, pose
