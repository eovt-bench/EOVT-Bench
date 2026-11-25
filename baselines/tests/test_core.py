from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from eovt_baseline.config import ControllerConfig, TrackerConfig
from eovt_baseline.controller import BBoxPIDController
from eovt_baseline.detectors import OracleBBoxDetector
from eovt_baseline.metrics import identity_metrics, occlusion_metrics
from eovt_baseline.paths import BASELINE_ROOT, writable_path
from eovt_baseline.result_schema import atomic_write_json, valid_final_result, validate_result
from eovt_baseline.runtime import layout_id, scene_category
from eovt_baseline.tracker import AppearanceTracker, bbox_iou
from eovt_baseline.types import Detection, TrackState


class ControllerTests(unittest.TestCase):
    def test_centered_small_target_moves_forward(self):
        controller = BBoxPIDController(ControllerConfig())
        detection = Detection((150, 100, 230, 300))
        action = controller.act(TrackState(detection, True, 0, "tracked"), (384, 384, 3))
        self.assertGreater(action[0], 0)
        self.assertAlmostEqual(float(action[2]), 0.0104166666, places=4)

    def test_loss_enters_search(self):
        controller = BBoxPIDController(ControllerConfig(search_yaw=0.4))
        action = controller.act(TrackState(None, False, 1, "lost"), (384, 384, 3))
        self.assertEqual(float(action[0]), 0.0)
        self.assertAlmostEqual(abs(float(action[2])), 0.4, places=5)


class DetectorTests(unittest.TestCase):
    def test_oracle_uses_robot_agent1_sensor(self):
        detector = OracleBBoxDetector({"min_pixels": 1})
        raw = {"agent_1_articulated_agent_jaw_rgb": np.zeros((384, 384, 4), dtype=np.uint8)}
        observations = {
            "agent_0_main_humanoid_detector_sensor": {
                "facing": np.asarray([0.0]), "box": np.zeros(4),
            },
            "agent_1_main_humanoid_detector_sensor": {
                "facing": np.asarray([1.0]), "box": np.asarray([100, 80, 200, 300]),
            },
        }
        _, detections = detector.detect(raw, observations, {"main_human_semantic_id": 1006})
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].bbox, (100.0, 80.0, 200.0, 300.0))


class TrackerTests(unittest.TestCase):
    def test_iou(self):
        self.assertAlmostEqual(bbox_iou((0, 0, 10, 10), (5, 5, 15, 15)), 25 / 175)

    def test_initializes_largest_person(self):
        tracker = AppearanceTracker(TrackerConfig(min_confidence=0.1))
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        state = tracker.update([Detection((0, 0, 10, 10), 0.9), Detection((20, 20, 80, 90), 0.8)], image)
        self.assertTrue(state.visible)
        self.assertEqual(state.detection.bbox, (20, 20, 80, 90))


class MetricTests(unittest.TestCase):
    def test_or_reacquisition(self):
        result = occlusion_metrics([True, True, False, False, True, True])
        self.assertEqual(result["reacquisition_success"], 1.0)
        self.assertEqual(result["recovery_steps"], 2)

    def test_identity(self):
        result = identity_metrics([
            {"condition": "same", "success": 1.0},
            {"condition": "swap", "target_retained": 0.0},
            {"condition": "swap", "target_retained": 1.0},
        ])
        self.assertEqual(result["same_success_rate"], 1.0)
        self.assertEqual(result["swap_success_rate"], 0.5)
        self.assertEqual(result["balanced_identity_accuracy"], 0.75)

    def test_identity_similar_protocol(self):
        result = identity_metrics([
            {"condition": "same", "success": 1.0},
            {"condition": "similar", "target_retained": 1.0},
            {"condition": "similar", "target_retained": 0.0},
            {"condition": "similar", "target_retained": 1.0},
        ])
        self.assertEqual(result["same_success_rate"], 1.0)
        self.assertAlmostEqual(result["similar_success_rate"], 2 / 3)
        self.assertAlmostEqual(result["balanced_identity_accuracy"], 5 / 6)


class SchemaAndPathTests(unittest.TestCase):
    def test_rejects_external_write(self):
        with self.assertRaises(ValueError):
            writable_path(BASELINE_ROOT.parent / "forbidden.json")

    def test_atomic_result_and_resume_validation(self):
        folder = BASELINE_ROOT / "tmp" / "unit_test"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "episode.json"
        atomic_write_json(path, {"success": 1.0, "following_rate": 0.5, "collision": 0.0})
        self.assertTrue(valid_final_result(path))
        self.assertEqual(validate_result(json.loads(path.read_text(encoding="utf-8"))), [])
        path.unlink()
        folder.rmdir()

    def test_stt_episode_metadata_is_derived(self):
        episode = type("Episode", (), {"episode_id": "036_industrial_layout_12_seed_20261004_000002", "info": {}})()
        self.assertEqual(scene_category(episode), "industrial")
        self.assertEqual(layout_id(episode), "036_industrial_layout_12_seed_20261004")

    def test_numpy_values_are_serialized(self):
        folder = BASELINE_ROOT / "tmp" / "unit_numpy"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "episode.json"
        atomic_write_json(path, {"success": np.float32(1), "following_rate": np.float32(0.5), "collision": np.int64(0)})
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["success"], 1.0)
        path.unlink()
        folder.rmdir()


if __name__ == "__main__":
    unittest.main()

