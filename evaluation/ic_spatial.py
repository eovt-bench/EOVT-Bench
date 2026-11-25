"""Frozen full-path geometry and elapsed-time IC rules. No model code."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import numpy as np
EPS = 1e-9
CONFIG_ROOT = Path(__file__).resolve().parents[1] / "configs/evaluation"
CONFIG = json.loads((CONFIG_ROOT / "ic_spatial_v0.2.json").read_text())

def wrap(x):
    return np.arctan2(np.sin(x), np.cos(x))

def degrees_gap(a, b):
    return np.abs(np.degrees(wrap(np.asarray(a) - np.asarray(b))))

def curve(points):
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if arc[-1] < 1e-10:
        return dict(points=points[:1].copy(), levels=np.array([0.0]), arc=arc)
    keep = np.r_[True, np.diff(arc) > 1e-10]
    count = max(2, int(math.ceil(
        arc[-1] / CONFIG["preprocessing"]["spatial_resample_max_step_m"]
    )) + 1)
    levels = np.linspace(0, arc[-1], count)
    sampled = np.column_stack([
        np.interp(levels, arc[keep], points[keep, j]) for j in range(2)
    ])
    return dict(points=sampled, levels=levels, arc=arc)

def arrays(rows):
    p = np.array([r["robot"]["position"] for r in rows], float)
    f = np.array([r["robot"]["forward"] for r in rows], float)
    assert np.all(np.linalg.norm(f[:, [0, 2]], axis=1) > 1e-8)
    result = dict(
        time=np.array([r["simulation_time_s"] for r in rows], float),
        step=np.array([r["step"] for r in rows], int),
        p3=p, p=p[:, [0, 2]], yaw=np.arctan2(f[:, 2], f[:, 0]),
        target3=np.array([r["target"]["position"] for r in rows], float),
        rot=np.array([r["robot"]["rotation_matrix_rows"] for r in rows], float),
    )
    result["target"] = result["target3"][:, [0, 2]]
    result["candidate"] = np.array([
        r["candidate"]["position"] if r.get("candidate") else [np.nan] * 3
        for r in rows
    ], float)[:, [0, 2]]
    result["robot_curve"] = curve(result["p"])
    result["target_curve"] = curve(result["target"])
    return result

def crop_same(rows, onset):
    times = np.array([r["simulation_time_s"] for r in rows])
    if onset > times[-1] + EPS or onset < times[0] - EPS:
        return []
    j = int(np.searchsorted(times, onset - EPS))
    if j < len(rows) and abs(times[j] - onset) <= EPS:
        return rows[j:]
    if j == 0 or j == len(rows):
        return []
    a, b = rows[j - 1], rows[j]
    alpha = (onset - times[j - 1]) / (times[j] - times[j - 1])
    boundary = copy.deepcopy(a)
    boundary["simulation_time_s"] = onset
    boundary["interpolated_activation_boundary"] = True
    for role in ("robot", "target"):
        for field in ("position", "forward", "rotation_matrix_rows"):
            x, y = np.array(a[role][field]), np.array(b[role][field])
            value = x + alpha * (y - x)
            if field == "forward":
                angle_a = math.atan2(x[2], x[0])
                angle_b = math.atan2(y[2], y[0])
                yaw = angle_a + alpha * float(wrap(angle_b - angle_a))
                value = np.array([math.cos(yaw), value[1], math.sin(yaw)])
                value /= np.linalg.norm(value)
            elif field == "rotation_matrix_rows":
                u, _, vh = np.linalg.svd(value)
                value = u @ np.diag([1., 1., np.linalg.det(u @ vh)]) @ vh
            boundary[role][field] = value.tolist()
    return [boundary] + rows[j:]

def correspondences(a, b, match, role="robot_curve"):
    """Map every raw A/B pose by fixed spatial DTW, never favorable heading."""
    ca, cb = a[role], b[role]
    maps_a = [[] for _ in ca["points"]]
    maps_b = [[] for _ in cb["points"]]
    for i, j in match["path"]:
        maps_a[i].append(j)
        maps_b[j].append(i)
    cfg = CONFIG["full_path_stage"]["stationary_phase_pairing"]

    def one(source, other, cs, co, mapping):
        selected, ambiguous, gaps = [], [], []
        for i, arc in enumerate(cs["arc"]):
            k = int(np.argmin(np.abs(cs["levels"] - arc)))
            other_level = float(np.median(co["levels"][mapping[k]]))
            nearest = int(np.argmin(np.abs(co["arc"] - other_level)))
            candidates = np.flatnonzero(
                np.abs(co["arc"] - co["arc"][nearest]) <= 1e-8
            )
            pos_error = np.linalg.norm(
                other["target3"][candidates] - source["target3"][i], axis=1
            )
            best = float(pos_error.min())
            near = candidates[pos_error <= best + cfg["near_equal_position_error_m"] + EPS]
            is_ambiguous = False
            if len(near) > 1 and np.ptp(other["time"][near]) > cfg["ambiguous_time_spread_s"]:
                headings = other["yaw"][near]
                spread = float(np.max(degrees_gap(headings[:, None], headings[None, :])))
                is_ambiguous = spread > cfg["ambiguous_heading_spread_deg"]
            ordered = sorted(near, key=lambda q: other["time"][q])
            j = int(ordered[len(ordered) // 2])
            selected.append(j)
            ambiguous.append(is_ambiguous)
            gaps.append(float(np.linalg.norm(other["target3"][j] - source["target3"][i])))
        return np.array(selected), np.array(ambiguous), np.array(gaps)

    return (
        one(a, b, ca, cb, maps_a),
        one(b, a, cb, ca, maps_b),
    )

def pose_summary(a, b, mapped):
    results = {}
    for name, source, other, maps in (
        ("same", a, b, mapped[0]), ("similar", b, a, mapped[1])
    ):
        indices, ambiguous, _ = maps
        gap = degrees_gap(source["yaw"], other["yaw"][indices])
        dt = np.diff(source["time"])
        good = ~ambiguous[1:] & (gap[1:] <= CONFIG["full_path_stage"]["body_heading_gap_limit_deg"] + EPS)
        total = float(dt.sum())
        results[name + "_heading_fraction"] = float(dt @ good / total) if total else 0.
        results[name + "_heading_mapping_coverage"] = float(dt @ (~ambiguous[1:]) / total) if total else 0.
        results[name + "_heading_gap_p90_deg"] = float(np.quantile(gap, .9))
    return results
