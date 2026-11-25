"""Frozen full-path geometry and elapsed-time IC rules. No model code."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import numpy as np
EPS = 1e-9
CONFIG_ROOT = Path(__file__).resolve().parents[1] / "configs/evaluation"
CFG = json.loads((CONFIG_ROOT / "ic_same_geometry_v0.2.json").read_text())

def frame_geometry(row):
    robot, target = row["robot"], row["target"]
    d = math.dist(robot["position"], target["position"])
    dx = target["position"][0] - robot["position"][0]
    dz = target["position"][2] - robot["position"][2]
    fx, fz = robot["forward"][0], robot["forward"][2]
    norm = math.hypot(dx, dz) * math.hypot(fx, fz)
    angle = None if norm <= 1e-12 else math.degrees(
        math.acos(max(-1.0, min(1.0, (dx*fx+dz*fz)/norm)))
    )
    condition = (
        CFG["final_distance_lower_m_inclusive"]-EPS <= d
        <= CFG["final_distance_upper_m_inclusive"]+EPS
        and angle is not None and angle <= CFG["body_original_angle_upper_deg"]+EPS
    )
    return dict(step=row["step"], simulation_time_s=row["simulation_time_s"],
                distance_m=d, body_original_angle_deg=angle,
                joint_following_condition=condition)

def path_length(rows, actor):
    return sum(math.hypot(
        b[actor]["position"][0]-a[actor]["position"][0],
        b[actor]["position"][2]-a[actor]["position"][2],
    ) for a, b in zip(rows, rows[1:]))

def assess(rows, info):
    if len(rows) < 2 or [r["step"] for r in rows] != list(range(len(rows))):
        raise ValueError("Incomplete observation sequence")
    for row in rows:
        if not math.isfinite(row["simulation_time_s"]):
            raise ValueError("Invalid simulation time")
        for actor in ("robot", "target"):
            if row[actor].get("errors"):
                raise ValueError("Recorded actor capture error")
            for field in ("position", "forward"):
                if len(row[actor][field]) != 3 or not all(math.isfinite(v) for v in row[actor][field]):
                    raise ValueError("Invalid position or heading")
    intervals = [b["simulation_time_s"]-a["simulation_time_s"] for a,b in zip(rows,rows[1:])]
    if min(intervals) <= 0 or max(intervals) > CFG["maximum_time_gap_s"]+EPS:
        raise ValueError("Missing or invalid timestamp interval")
    frames = [frame_geometry(row) for row in rows]
    end = frames[-1]["simulation_time_s"]
    beginning = end-CFG["tail_window_s"]
    observed = passed = 0.0
    tail = []
    for previous, current in zip(frames, frames[1:]):
        dt = max(0.0, current["simulation_time_s"]-max(previous["simulation_time_s"],beginning))
        if dt <= 0:
            continue
        observed += dt
        passed += dt*current["joint_following_condition"]
        tail.append(dict(**current,included_duration_s=dt))
    fraction = passed/observed if observed else 0.0
    minimum = min(f["distance_m"] for f in frames[1:])
    contact = minimum < CFG["existing_contact_proxy_distance_m_strictly_less_than"]
    robot_length, target_length = path_length(rows,"robot"),path_length(rows,"target")
    checks = dict(
        normal_end=info["end_reason"]==CFG["normal_end_reason_required"],
        no_close_contact_proxy=not contact,
        complete_tail=observed>=CFG["tail_window_s"]-1e-8,
        stable_tail_joint_condition=fraction>=CFG["tail_joint_condition_fraction_minimum"]-EPS,
        final_distance_in_range=CFG["final_distance_lower_m_inclusive"]-EPS<=frames[-1]["distance_m"]<=CFG["final_distance_upper_m_inclusive"]+EPS,
        final_heading_in_range=frames[-1]["body_original_angle_deg"] is not None and frames[-1]["body_original_angle_deg"]<=CFG["body_original_angle_upper_deg"]+EPS,
        robot_moved=robot_length>=CFG["minimum_robot_full_path_m"]-EPS,
        target_moved=target_length>=CFG["minimum_target_full_path_m"]-EPS,
    )
    original = info.get("original_same_success","")
    original = float(original) if original != "" else None
    reasons = dict(normal_end="未以正常episode_over结束",
                   no_close_contact_proxy="触发距离小于0.5米的接近碰撞代理",
                   complete_tail="末段记录不足0.48秒",
                   stable_tail_joint_condition="末0.48秒距离与朝向共同满足比例不足80%",
                   final_distance_in_range="最终距离不在1–3米内",
                   final_heading_in_range="最终朝向夹角超过45°或方向不可定义",
                   robot_moved="机器人完整路程不足0.08米",
                   target_moved="原目标完整路程不足0.08米")
    failed = [reasons[k] for k,v in checks.items() if not v]
    return dict(
        same_success_geometry=all(checks.values()),
        same_geometry_label="成功" if all(checks.values()) else "失败",
        original_same_success=original,
        original_same_success_source=info["same_success_evidence"],
        end_reason=info["end_reason"],end_reason_source=info["end_reason_source"],
        checks=checks,failed_checks=[k for k,v in checks.items() if not v],
        reason="满足独立Same几何资格；不等于恢复了原评价器成功记录" if not failed else "；".join(failed),
        final_distance_m=frames[-1]["distance_m"],
        final_angle_deg=frames[-1]["body_original_angle_deg"],
        tail_joint_fraction=fraction,tail_observed_duration_s=observed,
        minimum_distance_m=minimum,close_contact_proxy=contact,
        robot_full_path_m=robot_length,target_full_path_m=target_length,
        end_time_s=end,frame_count=len(frames),tail_evidence=tail,
    )
