from __future__ import annotations

import numpy as np

from .config import ControllerConfig
from .types import TrackState


class BBoxPIDController:
    def __init__(self, config: ControllerConfig):
        self.config = config
        self.search_steps = 0
        self.last_horizontal_sign = 1.0

    def reset(self) -> None:
        self.search_steps = 0
        self.last_horizontal_sign = 1.0

    def act(self, state: TrackState, image_shape: tuple[int, ...]) -> np.ndarray:
        if not state.visible or state.detection is None:
            direction = self.last_horizontal_sign
            if (self.search_steps // max(1, self.config.search_flip_steps)) % 2:
                direction *= -1.0
            self.search_steps += 1
            return np.asarray([0.0, 0.0, direction * self.config.search_yaw], dtype=np.float32)

        self.search_steps = 0
        height, width = image_shape[:2]
        detection = state.detection
        cx, _ = detection.center
        # Habitat's base-velocity yaw convention is the opposite of image-x.
        # Keep this identical to OmTrackVLA/baseline_agent.py:
        # error_t = 0.5 - center_x_normalized.
        x_error = (width / 2.0 - cx) / max(float(width), 1.0)
        self.last_horizontal_sign = 1.0 if x_error >= 0 else -1.0

        target_area = min(self.config.desired_area_pixels, 0.8 * width * height)
        area_error = (target_area - detection.area) / max(self.config.area_error_scale, 1.0)
        if abs(area_error) < self.config.area_deadband:
            area_error = 0.0
        forward = float(np.clip(self.config.forward_kp * area_error, -self.config.max_forward, self.config.max_forward))
        lateral = float(np.clip(self.config.lateral_kp * x_error, -self.config.max_lateral, self.config.max_lateral))
        yaw = float(np.clip(self.config.yaw_kp * x_error, -self.config.max_yaw, self.config.max_yaw))
        return np.asarray([forward, lateral, yaw], dtype=np.float32)

