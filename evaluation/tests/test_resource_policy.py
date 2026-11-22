"""Check missing/corrupt external files without downloading or mutating them."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("resource_checker", ROOT / "scripts/check_resources.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class ResourcePolicyTests(unittest.TestCase):
    def test_repository_metadata_is_complete_and_download_policy_external(self):
        report = CHECKER.audit_resources(group="metadata")
        self.assertEqual(report["status"], "PASS", report)
        config = json.loads((ROOT / "downloads.json").read_text())
        self.assertEqual(config["resources"]["assets"]["delivery"], "external_manual")
        self.assertNotIn("parts", config["resources"]["assets"])
        self.assertNotIn("filename", config["resources"]["assets"])

    def test_missing_corrupt_matching_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            content = b"valid external file"
            (root / "assets/resource_policy.json").write_text(json.dumps({
                "groups": [{"id": "fixture", "paths": ["assets/example"],
                            "delivery": "external_manual", "instructions": "fixture"}],
            }))
            manifest = {"files": [{"path": "assets/example/file", "bytes": len(content),
                                  "sha256": hashlib.sha256(content).hexdigest()}]}
            path = root / "assets/manifest.json"
            path.write_text(json.dumps(manifest))
            self.assertEqual(CHECKER.audit_resources(root)["status"], "FAIL")
            target = root / "assets/example/file"
            self.assertFalse(target.exists())
            target.parent.mkdir()
            target.write_bytes(b"x" * len(content))
            self.assertEqual(CHECKER.audit_resources(root)["groups"]["fixture"]["mismatched"][0]["reason"], "sha256")
            self.assertEqual(target.read_bytes(), b"x" * len(content))
            target.write_bytes(content)
            self.assertEqual(CHECKER.audit_resources(root)["status"], "PASS")
            manifest["files"][0]["path"] = "../outside"
            path.write_text(json.dumps(manifest))
            self.assertEqual(CHECKER.audit_resources(root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
