from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Detection:
    bbox: tuple[float, float, float, float]
    confidence: float = 1.0
    class_id: int = 0
    semantic_id: int | None = None
    appearance: np.ndarray | None = None
    metadata: dict[str, Any] | None = None

    @property
    def width(self) -> float:
        return max(0.0, self.bbox[2] - self.bbox[0])

    @property
    def height(self) -> float:
        return max(0.0, self.bbox[3] - self.bbox[1])

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.bbox[0] + self.bbox[2]) / 2.0, (self.bbox[1] + self.bbox[3]) / 2.0)


@dataclass
class TrackState:
    detection: Detection | None
    visible: bool
    lost_steps: int
    status: str
    association_score: float | None = None

