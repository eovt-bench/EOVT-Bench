from __future__ import annotations

from typing import Any

import numpy as np

from .config import BaselineConfig
from .controller import BBoxPIDController
from .detectors import build_detector
from .tracker import AppearanceTracker


class BaselineAgent:
    def __init__(self, config: BaselineConfig, *, device_override: str | None = None):
        self.config = config
        self.detector = build_detector(config.detector, device_override=device_override)
        self.tracker = AppearanceTracker(config.tracker)
        self.controller = BBoxPIDController(config.controller)

    def reset(self) -> None:
        self.tracker.reset()
        self.controller.reset()

    def act(
        self,
        raw_observations: dict[str, Any],
        task_observations: dict[str, Any],
        episode_info: dict[str, Any],
    ) -> tuple[np.ndarray, dict[str, Any]]:
        image, detections = self.detector.detect(raw_observations, task_observations, episode_info)
        state = self.tracker.update(detections, image)
        action = self.controller.act(state, image.shape)
        debug = {
            "visible": state.visible,
            "tracker_status": state.status,
            "lost_steps": state.lost_steps,
            "association_score": state.association_score,
            "bbox": list(state.detection.bbox) if state.detection else None,
            "num_detections": len(detections),
            "action": [float(x) for x in action],
        }
        return action, debug
