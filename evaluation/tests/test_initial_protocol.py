import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ic_behavior import score_event
from or_visibility import ORConfig, score_event as score_or


def _row(step, robot_x, target_x, heading=0.0, pixels=5000):
    return {
        "step": step,
        "target_pixels": pixels,
        "image_height": 384,
        "image_width": 384,
        "target_distance_m": abs(target_x - robot_x),
        "robot_position": [robot_x, 0.0, 0.0],
        "original_position": [target_x, 0.0, 0.0],
        "robot_heading_rad": heading,
    }


class InitialProtocolTests(unittest.TestCase):
    def test_or_requires_actual_loss_and_stable_recovery(self):
        rows = []
        for step in range(20):
            visible = not 5 <= step <= 7
            pixels = 5000 if visible else 0
            rows.append({
                "step": step,
                "target_pixels": pixels,
                "image_height": 384,
                "image_width": 384,
                "target_distance_m": 1.5,
                "collision": False,
            })
        scored = score_or(rows, ORConfig(recovery_window_steps=12))
        self.assertTrue(scored["actual_loss"])
        self.assertTrue(scored["opportunity"])
        self.assertTrue(scored["recovered"])
        self.assertEqual(scored["rsr"], 1.0)

    def test_ic_does_not_use_otpr(self):
        same = {"success": 1, "collision": 0, "records": [_row(i, i * 0.1, i * 0.1 + 1.5) for i in range(10)]}
        similar_rows = [_row(i, i * 0.1, i * 0.1 + 1.5) for i in range(10)]
        similar = [{"records": similar_rows, "target_dominance_rate": 0.0} for _ in range(3)]
        result = score_event({"same": same, "similar": similar})
        self.assertEqual(result["similar_follow_original_count"], 3)
        self.assertEqual(result["effective_follow_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
