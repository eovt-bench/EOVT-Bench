"""Current baseline evidence and resume contract, independent of Habitat."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "baselines"))
sys.path.insert(0, str(ROOT / "evaluation"))
from eovt_baseline.current_evaluator import resumable
from shared_analysis import load_json_records


class EvidenceContractTests(unittest.TestCase):
    def test_resume_requires_current_protocol_matching_execution_and_intact_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "event_evidence" / "attempt_1" / "frames.jsonl"
            evidence.parent.mkdir(parents=True)
            evidence.write_text('{"step":0}\n')
            result = root / "event.json"
            data = {
                "protocol_version": "eovt-or-visibility-v0.2",
                "execution_fingerprint": "frozen",
                "actual_loss": False, "opportunity": False,
                "recovered": False, "censored": False,
                "rsr": None, "vor": None, "crr": None,
                "evidence": str(evidence.relative_to(root)),
                "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
            result.write_text(json.dumps(data))
            self.assertTrue(resumable(result, "or", "frozen", root))
            self.assertFalse(resumable(result, "or", "different", root))
            self.assertFalse(resumable(result, "ic", "frozen", root))
            evidence.write_text('{"step":1}\n')
            self.assertFalse(resumable(result, "or", "frozen", root))
            for bad in ("[]", "null", "invalid"):
                result.write_text(bad)
                self.assertFalse(resumable(result, "or", "frozen", root))

    def test_auxiliary_attempts_are_not_population_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "event.json").write_text('{"episode_id":"event"}')
            folder = root / "event_evidence" / "attempt_1" / "same"
            folder.mkdir(parents=True)
            (folder / "camera_info.json").write_text("{}")
            (folder.parent / "ic_event.json").write_text('{"same":{}}')
            records, errors = load_json_records(root)
            self.assertEqual(errors, [])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["data"]["episode_id"], "event")


if __name__ == "__main__":
    unittest.main()
