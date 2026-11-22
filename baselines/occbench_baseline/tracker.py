from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .appearance import cosine_similarity, crop_histogram
from .config import TrackerConfig
from .types import Detection, TrackState


def bbox_iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


class AppearanceTracker:
    def __init__(self, config: TrackerConfig):
        self.config = config
        self.last: Detection | None = None
        self.template: np.ndarray | None = None
        self.lost_steps = 0

    def reset(self) -> None:
        self.last = None
        self.template = None
        self.lost_steps = 0

    @staticmethod
    def _center_score(detection: Detection, image_shape: tuple[int, ...]) -> float:
        height, width = image_shape[:2]
        cx, cy = detection.center
        distance = math.hypot((cx - width / 2) / max(width, 1), (cy - height / 2) / max(height, 1))
        return max(0.0, 1.0 - distance / math.sqrt(0.5))

    def update(self, detections: list[Detection], image: np.ndarray) -> TrackState:
        eligible = [d for d in detections if d.confidence >= self.config.min_confidence]
        for index, detection in enumerate(eligible):
            if detection.appearance is None:
                eligible[index] = replace(detection, appearance=crop_histogram(image, detection.bbox))

        if not eligible:
            self.lost_steps += 1
            return TrackState(None, False, self.lost_steps, "lost")

        if self.last is None:
            selected = max(
                eligible,
                key=lambda item: (item.area, self._center_score(item, image.shape), item.confidence),
            )
            score = 1.0
            status = "initialized"
        else:
            candidates: list[tuple[float, Detection]] = []
            for item in eligible:
                iou = bbox_iou(self.last.bbox, item.bbox)
                center = self._center_score(item, image.shape)
                appearance = (cosine_similarity(self.template, item.appearance) + 1.0) / 2.0
                if self.lost_steps > 0:
                    # Re-identification should rely more on appearance than stale geometry.
                    score = 0.15 * iou + 0.15 * center + 0.70 * appearance
                else:
                    score = (
                        self.config.iou_weight * iou
                        + self.config.center_weight * center
                        + self.config.appearance_weight * appearance
                    )
                candidates.append((score, item))
            score, selected = max(candidates, key=lambda pair: pair[0])
            if score < self.config.match_threshold:
                self.lost_steps += 1
                if self.lost_steps <= self.config.lost_tolerance:
                    return TrackState(None, False, self.lost_steps, "uncertain", score)
            status = "reacquired" if self.lost_steps else "tracked"

        self.last = selected
        self.lost_steps = 0
        if self.template is None:
            self.template = selected.appearance
        elif selected.appearance is not None:
            blended = 0.9 * self.template + 0.1 * selected.appearance
            norm = float(np.linalg.norm(blended))
            self.template = blended / norm if norm > 0 else blended
        return TrackState(selected, True, 0, status, score)

