"""Elapsed-time observation opportunities from synchronized simulator truth."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import math
from or_visibility_legacy_v01 import ORConfig, enrich


@dataclass(frozen=True)
class Config:
    version: str = "eovt-or-visibility-v0.2"
    visible_min_pixels: int = 16
    visible_fraction: float = 0.001
    initial_visible_steps: int = 5
    loss_steps: int = 3
    recovery_window_steps: int = 50
    image_fraction_min: float = 0.003
    image_fraction_max: float = 0.40
    target_visibility_min: float = 0.25
    opportunity_distance_min_m: float = 0.8
    opportunity_duration_s: float = 0.2
    following_duration_s: float = 0.4
    maximum_evidence_gap_s: float = 0.2
    follow_distance_m: float = 3.0
    follow_pixel_fraction_lower: float = 3000/(384*384)
    follow_pixel_fraction_upper: float = 0.30


def _first_run(values, length, start=0, end=None):
    streak = 0
    for i in range(start, len(values) if end is None else end+1):
        streak = streak+1 if values[i] else 0
        if streak >= length:
            return i-length+1, i
    return None


def _timed_run(rows, values, duration, start, end, max_gap):
    onset = None
    for i in range(start, end+1):
        if not values[i]:
            onset = None
            continue
        if onset is None or (i > start and rows[i]["simulation_time_s"]-rows[i-1]["simulation_time_s"] > max_gap):
            onset = i
        if rows[i]["simulation_time_s"]-rows[onset]["simulation_time_s"]+1e-9 >= duration:
            return onset, i
    return None


def score_event(raw_rows, config=None):
    cfg = config or Config()
    if not raw_rows:
        raise ValueError("OR synchronized evidence is empty")
    rows = []
    for raw in raw_rows:
        row = enrich(raw, ORConfig(visible_min_pixels=cfg.visible_min_pixels,
                                   visible_fraction=cfg.visible_fraction,
                                   follow_distance_m=cfg.follow_distance_m,
                                   follow_pixel_fraction_lower=cfg.follow_pixel_fraction_lower,
                                   follow_pixel_fraction_upper=cfg.follow_pixel_fraction_upper))
        timestamp = raw.get("simulation_time_s",raw.get("world_time_s"))
        if timestamp is None or not math.isfinite(float(timestamp)):
            raise ValueError("Actual OR simulation timestamps are required")
        if "target_visibility_ratio" not in raw:
            raise ValueError("OR opportunity requires full target projection evidence")
        ratio = raw["target_visibility_ratio"]
        if ratio is not None and (not math.isfinite(ratio) or not 0 <= ratio <= 1):
            raise ValueError("Invalid target visibility fraction")
        row["simulation_time_s"] = float(timestamp)
        row["opportunity_candidate"] = bool(
            row["visible"] and ratio is not None and ratio >= cfg.target_visibility_min
            and cfg.image_fraction_min <= row["target_fraction"] <= cfg.image_fraction_max
            and row["target_distance_m"] >= cfg.opportunity_distance_min_m)
        rows.append(row)
    if [r["step"] for r in rows] != list(range(len(rows))):
        raise ValueError("OR evidence must begin at frame 0 without missing steps")
    if any(b["simulation_time_s"] <= a["simulation_time_s"] or
           b["simulation_time_s"]-a["simulation_time_s"] > cfg.maximum_evidence_gap_s+1e-9
           for a,b in zip(rows,rows[1:])):
        raise ValueError("Missing or invalid OR observation timestamps")
    visible = [r["visible"] for r in rows]
    result = dict(protocol_version=cfg.version, protocol=asdict(cfg),
                  actual_loss=False,opportunity=False,recovered=False,censored=False,
                  rsr=None,vor=None,crr=None,lost_step=None,reappeared_step=None,
                  recovery_confirmed_step=None,recovery_delay_steps=None,
                  recovery_after_opportunity_s=None)
    initial = _first_run(visible,cfg.initial_visible_steps)
    if initial is None:
        return dict(result,status="initial_visibility_not_established")
    loss = _first_run([not v for v in visible],cfg.loss_steps,initial[1]+1)
    if loss is None:
        return dict(result,status="no_runtime_loss")
    onset, confirmed = loss
    end = min(onset+cfg.recovery_window_steps,len(rows)-1)
    collision = next((i for i in range(confirmed,end+1) if rows[i].get("collision")),None)
    if collision is not None:
        end = collision
    terminal_reason = rows[end].get("termination_reason")
    endpoint = (end == onset+cfg.recovery_window_steps or rows[end].get("env_episode_over")
                or rows[end].get("collision") or terminal_reason in {
                    "collision","original_distance_abort","max_steps",
                    "environment_episode_over","Lost","Collision","episode_over"})
    unknown_projection = any(r["target_visibility_ratio"] is None for r in rows[confirmed+1:end+1])
    result.update(actual_loss=True,lost_step=onset,loss_confirmed_step=confirmed,
                  lost_time_s=rows[onset]["simulation_time_s"],window_end_step=end,
                  unknown_projection=unknown_projection,censored=not endpoint or unknown_projection,
                  rsr=0.0 if endpoint and not unknown_projection else None,
                  vor=0.0 if endpoint and not unknown_projection else None)
    opportunity = _timed_run(rows,[r["opportunity_candidate"] for r in rows],
                            cfg.opportunity_duration_s,confirmed+1,end,cfg.maximum_evidence_gap_s)
    if opportunity is None:
        return dict(result,status="censored_before_opportunity" if result["censored"] else "no_observation_opportunity")
    begin, opp_confirmed = opportunity
    result.update(opportunity=True,vor=1.0,reappeared_step=begin,
                  reappearance_confirmed_step=opp_confirmed,
                  opportunity_time_s=rows[opp_confirmed]["simulation_time_s"])
    if endpoint:
        # Once an opportunity is confirmed, mask/distance evidence suffices
        # to decide following; unrelated projection gaps cannot censor it.
        result.update(censored=False,rsr=0.0)
    recovery = _timed_run(rows,[r["following"] for r in rows],cfg.following_duration_s,
                         opp_confirmed+1,end,cfg.maximum_evidence_gap_s)
    if recovery is None:
        result["crr"] = 0.0 if result["rsr"] == 0.0 else None
        return dict(result,status="censored_before_recovery" if result["censored"] else "visible_but_not_recovered")
    start, finish = recovery
    result.update(recovered=True,censored=False,rsr=1.0,crr=1.0,
                  recovery_start_step=start,recovery_confirmed_step=finish,
                  recovery_delay_steps=finish-onset,
                  recovery_time_s=rows[finish]["simulation_time_s"],
                  recovery_after_opportunity_s=rows[finish]["simulation_time_s"]-rows[opp_confirmed]["simulation_time_s"])
    return dict(result,status="recovered")


def aggregate_events(results):
    """Keep actual-loss denominators and unknown outcomes explicit."""
    loss=[r for r in results if r["actual_loss"]]
    opportunity=[r for r in loss if r["opportunity"]]
    recovered=[r for r in loss if r["recovered"]]
    unknown=[r for r in loss if r["rsr"] is None]
    unknown_opportunity=[r for r in loss if r["vor"] is None]
    return dict(protocol_version=Config.version,total_events=len(results),
        actual_loss_events=len(loss),opportunity_events=len(opportunity),
        recovered_events=len(recovered),censored_events=len(unknown),
        no_runtime_loss_events=sum(r["status"]=="no_runtime_loss" for r in results),
        rsr=len(recovered)/len(loss) if loss and not unknown else None,
        vor=len(opportunity)/len(loss) if loss and not unknown_opportunity else None,
        crr=len(recovered)/len(opportunity) if opportunity and not any(r["crr"] is None for r in opportunity) else None,
        rsr_bounds=[len(recovered)/len(loss),(len(recovered)+len(unknown))/len(loss)] if loss else None,
        mrs=sum(r["recovery_delay_steps"] for r in recovered)/len(recovered) if recovered else None)
