from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .paths import BASELINE_ROOT, resolve_readonly
from .types import Detection


def find_sensor(observations: dict[str, Any], suffix: str) -> np.ndarray:
    for key, value in observations.items():
        if key == suffix or key.endswith(suffix):
            return np.asarray(value)
    raise KeyError(f"sensor ending in {suffix!r} was not found; available={list(observations)}")


class OracleBBoxDetector:
    """Use OccBench's target-specific detector observation (oracle/sanity baseline)."""

    def __init__(self, config: dict[str, Any]):
        self.min_pixels = int(config.get("min_pixels", 1))

    def detect(
        self,
        raw_observations: dict[str, Any],
        task_observations: dict[str, Any],
        episode_info: dict[str, Any],
    ) -> tuple[np.ndarray, list[Detection]]:
        image = find_sensor(raw_observations, "articulated_agent_jaw_rgb")
        # The task duplicates this sensor for every articulated agent.  The
        # first suffix match is agent_0's observation, which has no robot jaw
        # camera and therefore returns an empty box.  OmTrackVLA explicitly
        # uses the robot-mounted agent_1 sensor; do the same here.
        detector = task_observations.get("agent_1_main_humanoid_detector_sensor")
        if detector is None:
            for key, value in task_observations.items():
                if key.startswith("agent_1_") and key.endswith("main_humanoid_detector_sensor"):
                    detector = value
                    break
        if detector is None:
            raise KeyError(f"main humanoid detector not found; available={list(task_observations)}")
        if isinstance(detector, dict):
            facing = np.asarray(detector.get("facing", False)).reshape(-1)
            if not (facing.size and float(facing[0]) > 0):
                return image, []
            bbox = tuple(float(x) for x in detector.get("box", (0, 0, 0, 0)))
        else:
            flat = np.asarray(detector).reshape(-1)
            if flat.size < 5 or float(flat[0]) <= 0:
                return image, []
            bbox = tuple(float(x) for x in flat[1:5])
        if max(bbox) <= 0:
            return image, []
        semantic_id = episode_info.get("main_human_semantic_id", episode_info.get("main_human_id", 100))
        return image, [Detection(bbox=bbox, confidence=1.0, semantic_id=int(semantic_id))]


class UltralyticsPersonDetector:
    def __init__(self, config: dict[str, Any], *, device_override: str | None = None):
        weights = resolve_readonly(config.get("weights", "../assets/detectors/yolo11x.pt"))
        if not weights.exists():
            raise FileNotFoundError(f"YOLO weights not found: {weights}")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("rgb_tracker_pid requires the existing environment to provide ultralytics") from exc
        self.model = YOLO(str(weights))
        self.confidence = float(config.get("confidence", 0.25))
        self.iou = float(config.get("iou", 0.7))
        self.device = device_override or str(config.get("device", "cuda:0"))

    def detect(
        self,
        raw_observations: dict[str, Any],
        task_observations: dict[str, Any],
        episode_info: dict[str, Any],
    ) -> tuple[np.ndarray, list[Detection]]:
        image = find_sensor(raw_observations, "articulated_agent_jaw_rgb")[..., :3]
        detector_image = image[..., ::-1]
        result = self.model.predict(
            source=detector_image,
            classes=[0],
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )[0]
        detections: list[Detection] = []
        if result.boxes is not None:
            xyxy = result.boxes.xyxy.detach().cpu().numpy()
            conf = result.boxes.conf.detach().cpu().numpy()
            cls = result.boxes.cls.detach().cpu().numpy()
            for box, score, class_id in zip(xyxy, conf, cls):
                detections.append(
                    Detection(tuple(float(value) for value in box), float(score), int(class_id))
                )
        return image, detections


def build_detector(config: dict[str, Any], *, device_override: str | None = None):
    kind = str(config.get("type", "oracle")).lower()
    if kind == "oracle":
        return OracleBBoxDetector(config)
    if kind == "ultralytics":
        return UltralyticsPersonDetector(config, device_override=device_override)
    raise ValueError(f"unsupported detector type: {kind}")

