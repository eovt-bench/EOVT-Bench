"""Validate published task semantics without depending on installed scene assets."""
import gzip
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MetadataProtocolTests(unittest.TestCase):
    def test_canonical_event_descriptions_and_fixed_identity_assignments(self):
        people = json.loads((ROOT / "assets/humanoids/appearance_top3.json").read_text())["persons"]
        for task, name in (
            ("OR", "Post-Occlusion Target Reacquisition"),
            ("IC", "Post-Occlusion Identity Consistency"),
        ):
            with gzip.open(ROOT / f"episodes/{task}/val/val.json.gz", "rt") as handle:
                episodes = json.load(handle)["episodes"]
            self.assertEqual(len(episodes), 630)
            for episode in episodes:
                event = episode["info"]["eovt_task"]
                self.assertEqual(event["task_name"], name)
                self.assertEqual(event["task_version"], "eovt-or-ic-v0.2")
                self.assertEqual(event["action_mode"], "closed_loop_model_actions_executed")
                if task == "IC":
                    self.assertEqual(episode["eovt_event"], event)
                    trials = event["identity_trials"]
                    self.assertEqual(len(trials), 4)
                    self.assertEqual(sum(t["condition"] == "same" for t in trials), 1)
                    self.assertFalse(any("expected_label" in t for t in trials))
                    target = episode["info"]["main_humanoid_name"]
                    actual = [t["actor_name_after_occlusion"] for t in trials if t["condition"] == "similar"]
                    self.assertEqual(actual, [p["name"] for p in people[target]["top3_similar"]])


if __name__ == "__main__":
    unittest.main()
