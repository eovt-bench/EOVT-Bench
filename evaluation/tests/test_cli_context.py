"""The public scorer must preserve grouping metadata used by bootstrap."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CLIContextTests(unittest.TestCase):
    def test_or_wrapper_context_survives_scoring(self):
        rows = [
            {"step": i, "simulation_time_s": i * 0.05, "target_pixels": 6000,
             "image_height": 384, "image_width": 384, "target_distance_m": 1.5,
             "target_visibility_ratio": 1.0, "collision": False}
            for i in range(10)
        ]
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "input.json", Path(directory) / "score.json"
            source.write_text(json.dumps({
                "episode_id": "custom-event", "layout_id": "shared-layout",
                "scene_category": "road", "records": rows,
            }))
            subprocess.run([
                sys.executable, str(ROOT / "evaluation/score_or_ic.py"), "or",
                str(source), "--output", str(output),
            ], check=True, capture_output=True, text=True)
            scored = json.loads(output.read_text())
            self.assertEqual(scored["layout_id"], "shared-layout")
            self.assertEqual(scored["episode_id"], "custom-event")
            self.assertEqual(scored["scene_category"], "road")
            self.assertEqual(scored["status"], "no_runtime_loss")


if __name__ == "__main__":
    unittest.main()
