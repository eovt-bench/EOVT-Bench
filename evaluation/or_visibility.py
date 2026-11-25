"""Versioned OR visibility and reacquisition scorer.

The scorer separates three observations:
1. an actual runtime loss of the target,
2. a confirmed reappearance opportunity, and
3. stable recovery of effective following.

It uses synchronized target-instance pixels and robot-target distance. It does
not infer visibility from the existence of later records and does not use a
model's target-selection output as an evaluator input.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


@dataclass(frozen=True)
class ORConfig:
    version: str = "eovt-or-initial-v0.1"
    visible_fraction: float = 0.001
    visible_min_pixels: int = 16
    initial_visible_steps: int = 5
    loss_steps: int = 3
    reappearance_steps: int = 2
    recovery_steps: int = 5
    recovery_window_steps: int = 50
    follow_distance_m: float = 3.0
    follow_pixel_fraction_lower: float = 3000 / (384 * 384)
    follow_pixel_fraction_upper: float = 0.3


def _first_run(values: list[bool], length: int, begin: int = 0, end: int | None = None):
    if not values:
        return None
    last = len(values) - 1 if end is None else min(end, len(values) - 1)
    streak = 0
    for index in range(begin, last + 1):
        streak = streak + 1 if values[index] else 0
        if streak >= length:
            return index - length + 1, index
    return None


def enrich(row: dict[str, Any], config: ORConfig) -> dict[str, Any]:
    required = ("step", "target_pixels", "image_height", "image_width", "target_distance_m")
    if any(name not in row or row[name] is None for name in required):
        raise ValueError(f"Missing OR camera/state evidence: {required}")
    height, width = row["image_height"], row["image_width"]
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (height, width)):
        raise ValueError("Image dimensions must be positive integers")
    pixels = row["target_pixels"]
    if isinstance(pixels, bool) or not isinstance(pixels, int) or not 0 <= pixels <= height * width:
        raise ValueError("Invalid target-instance pixel count")
    distance = float(row["target_distance_m"])
    if not math.isfinite(distance) or distance < 0:
        raise ValueError("Invalid target distance")
    fraction = pixels / (height * width)
    visible_threshold = max(config.visible_min_pixels, math.ceil(config.visible_fraction * height * width))
    visible = pixels >= visible_threshold
    following = (
        visible
        and distance <= config.follow_distance_m
        and fraction > config.follow_pixel_fraction_lower
        and fraction < config.follow_pixel_fraction_upper
        and not bool(row.get("collision", False))
    )
    return {
        **row,
        "target_fraction": fraction,
        "visible_pixel_threshold": visible_threshold,
        "visible": visible,
        "following": following,
    }


def score_event(rows: list[dict[str, Any]], config: ORConfig | None = None) -> dict[str, Any]:
    config = config or ORConfig()
    if not rows:
        raise ValueError("Cannot score an empty OR rollout")
    enriched = [enrich(row, config) for row in rows]
    steps = [int(row["step"]) for row in enriched]
    if steps != list(range(steps[0], steps[0] + len(steps))) or steps[0] != 0:
        raise ValueError("OR rows must start at step 0 and be contiguous")
    visible = [bool(row["visible"]) for row in enriched]
    following = [bool(row["following"]) for row in enriched]
    result: dict[str, Any] = {
        "protocol_version": config.version,
        "actual_loss": False,
        "opportunity": False,
        "recovered": False,
        "rsr": None,
        "vor": None,
        "crr": None,
        "lost_step": None,
        "loss_confirmed_step": None,
        "reappeared_step": None,
        "reappearance_confirmed_step": None,
        "recovery_start_step": None,
        "recovery_confirmed_step": None,
        "recovery_delay_steps": None,
        "censored": False,
        "status": None,
    }
    initial = _first_run(visible, config.initial_visible_steps)
    if initial is None:
        result["status"] = "initial_visibility_not_established"
        return result
    loss = _first_run([not value for value in visible], config.loss_steps, initial[1] + 1)
    if loss is None:
        result["status"] = "no_runtime_loss"
        return result
    onset, confirmed = loss
    deadline = onset + config.recovery_window_steps
    last = min(deadline, len(enriched) - 1)
    endpoint_observed = (
        last >= deadline
        or bool(enriched[last].get("collision", False))
        or bool(enriched[last].get("env_episode_over", False))
    )
    result.update(
        actual_loss=True,
        lost_step=onset,
        loss_confirmed_step=confirmed,
        rsr=0.0 if endpoint_observed else None,
        vor=0.0 if endpoint_observed else None,
        censored=not endpoint_observed,
    )
    opportunity = _first_run(visible, config.reappearance_steps, confirmed + 1, last)
    if opportunity is None:
        result["status"] = "no_reappearance_observed" if endpoint_observed else "censored_before_reappearance"
        return result
    begin, opportunity_confirmed = opportunity
    result.update(
        opportunity=True,
        vor=1.0,
        reappeared_step=begin,
        reappearance_confirmed_step=opportunity_confirmed,
    )
    recovery = _first_run(following, config.recovery_steps, opportunity_confirmed + 1, last)
    if recovery is None:
        result["status"] = "visible_but_not_recovered" if endpoint_observed else "censored_before_recovery"
        return result
    recovery_start, recovery_confirmed = recovery
    result.update(
        recovered=True,
        rsr=1.0,
        crr=1.0,
        recovery_start_step=recovery_start,
        recovery_confirmed_step=recovery_confirmed,
        recovery_delay_steps=recovery_confirmed - onset,
        censored=False,
        status="recovered",
    )
    return result


def aggregate_events(results: list[dict[str, Any]]) -> dict[str, Any]:
    loss = [row for row in results if row.get("actual_loss")]
    opportunity = [row for row in loss if row.get("opportunity")]
    recovered = [row for row in loss if row.get("recovered")]
    censored = [row for row in loss if row.get("censored")]
    return {
        "protocol_version": ORConfig.version,
        "events": len(results),
        "actual_loss_events": len(loss),
        "opportunity_events": len(opportunity),
        "recovered_events": len(recovered),
        "censored_events": len(censored),
        "rsr": len(recovered) / len(loss) if loss and not censored else None,
        "vor": len(opportunity) / len(loss) if loss else None,
        "crr": len(recovered) / len(opportunity) if opportunity and not censored else None,
        "mrs": (
            sum(float(row["recovery_delay_steps"]) for row in recovered)
            / len(recovered)
            if recovered
            else None
        ),
    }


def config_dict(config: ORConfig | None = None) -> dict[str, Any]:
    return asdict(config or ORConfig())
