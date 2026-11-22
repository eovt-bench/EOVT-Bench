from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import BASELINE_ROOT, resolve_readonly


@dataclass
class TrackerConfig:
    min_confidence: float = 0.25
    iou_weight: float = 0.4
    center_weight: float = 0.2
    appearance_weight: float = 0.4
    match_threshold: float = 0.28
    lost_tolerance: int = 30


@dataclass
class ControllerConfig:
    # Defaults mirror OmTrackVLA/baseline_agent.py.
    forward_kp: float = 1.0
    yaw_kp: float = 2.0
    lateral_kp: float = 0.5
    desired_area_pixels: float = 30000.0
    area_error_scale: float = 10000.0
    area_deadband: float = 0.5
    max_forward: float = 3.0
    max_lateral: float = 0.5
    max_yaw: float = 1.0
    search_yaw: float = 0.0
    search_flip_steps: int = 30


@dataclass
class EvaluationConfig:
    max_steps: int = 300
    too_far_distance: float = 4.0
    too_far_patience: int = 20


@dataclass
class BaselineConfig:
    variant: str
    detector: dict[str, Any] = field(default_factory=dict)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    controller: ControllerConfig = field(default_factory=ControllerConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)


def load_config(variant: str, config_path: str | Path | None = None) -> BaselineConfig:
    path = resolve_readonly(config_path or BASELINE_ROOT.parent / "configs" / "baselines" / f"{variant}.json")
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return BaselineConfig(
        variant=raw["variant"],
        detector=dict(raw.get("detector", {})),
        tracker=TrackerConfig(**raw.get("tracker", {})),
        controller=ControllerConfig(**raw.get("controller", {})),
        evaluation=EvaluationConfig(**raw.get("evaluation", {})),
    )
