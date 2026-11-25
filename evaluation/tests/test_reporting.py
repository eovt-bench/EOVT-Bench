"""Regression cases for metric eligibility and current IC result validation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation"))
sys.path.insert(0, str(ROOT / "baselines"))
from reporting import summarize_directory
from eovt_baseline.result_schema import validate_result, valid_final_result
from eovt_baseline.runner import build_parser, require_supported_protocol


class ReportingTests(unittest.TestCase):
    def test_ic_does_not_require_legacy_bia(self):
        data = {
            "success": 1, "following_rate": 0.8, "collision": 0,
            "identity_trial_results": [
                {"condition": "same", "success": 1, "collision": 0},
                *[{"condition": "similar", "success": 1, "collision": 0, "target_dominance": d}
                  for d in (0.2, 0.8, 0.5)],
            ],
        }
        self.assertEqual(validate_result(data, "ic"), [])

    def test_completed_failure_is_included_and_info_is_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"episode_id": "case", "layout": "layout", "success": 0,
                    "following_rate": 0.25, "collision": 0, "finish": False, "status": "Lost"}
            (root / "case.json").write_text(json.dumps(data))
            (root / "case_info.json").write_text(json.dumps({"success": 1}))
            report = summarize_directory(root, "stt", 0)
            self.assertEqual(report["parsed_final_records"], 1)
            self.assertEqual(report["summary"]["sr"], 0)
            self.assertEqual(report["summary"]["tr"], 25)

    def test_boolean_cannot_be_resume_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(json.dumps({"success": True, "following_rate": 0.5, "collision": 0}))
            self.assertFalse(valid_final_result(path))

    def test_nonobject_json_cannot_be_resume_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text("[]")
            self.assertFalse(valid_final_result(path))

    def test_duplicate_ids_fail_loudly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"episode_id": "duplicate", "success": 1, "following_rate": 1, "collision": 0}
            for name in ("a.json", "b.json"):
                (root / name).write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                summarize_directory(root, "stt", 0)

    def test_legacy_or_requires_explicit_opt_in_and_keeps_its_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"episode_id": "case", "layout": "layout_1",
                    "success": 0, "following_rate": 0, "collision": 0,
                    "rsr": 0, "vor": 1, "online_summary_protocol": "legacy-facing-k1"}
            (root / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "allow-legacy"):
                summarize_directory(root, "or", 0)
            report = summarize_directory(root, "or", 0, allow_legacy=True)
            self.assertEqual(report["input_protocol_versions"], ["legacy-facing-k1"])
            self.assertEqual(report["summary"]["rsr"], 0)

    def test_bootstrap_cannot_use_custom_event_as_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"episode_id": "arbitrary-event", "success": 1,
                    "following_rate": 1, "collision": 0}
            (root / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "missing layout"):
                summarize_directory(root, "stt", 10)
            data["layout_id"] = "shared-layout"
            (root / "case.json").write_text(json.dumps(data))
            report = summarize_directory(root, "stt", 10)
            self.assertEqual(report["layout_count"], 1)

    def test_current_ic_bad_trial_object_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"identity_evaluator_version": "eovt-ic-behavior-v0.2",
                    "same_success": True, "similar_results": [None] * 3}
            (root / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "three binary"):
                summarize_directory(root, "ic", 0)

    def test_baseline_current_protocol_is_default_and_legacy_is_explicit(self):
        for task in ("or", "ic"):
            args = build_parser().parse_args(["--variant", "oracle_pid", "--task", task])
            self.assertFalse(args.legacy_online_metrics)
            require_supported_protocol(args)
            args.legacy_online_metrics = True
            require_supported_protocol(args)
        require_supported_protocol(
            build_parser().parse_args(["--variant", "oracle_pid", "--task", "stt"])
        )
