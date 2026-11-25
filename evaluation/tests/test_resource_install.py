"""Verify a real empty-directory resource installation without large assets."""
import contextlib
import hashlib
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/download_resources.py"
SPEC = importlib.util.spec_from_file_location("resource_installer", SCRIPT)
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class ResourceInstallationTests(unittest.TestCase):
    def test_external_manual_resource_cannot_use_release_downloader(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(INSTALLER.subprocess, "run") as download:
                with self.assertRaises(ValueError):
                    INSTALLER.download_archive(
                        Path(directory), {"delivery": "external_manual"}, {}, workers=1,
                    )
                download.assert_not_called()

    def multipart_fixture(self, directory):
        content = b"fixed multipart resource: metadata order must be preserved"
        chunks = (content[:19], content[19:])
        parts = []
        for name, chunk in zip(("piece-z.bin", "piece-a.bin"), chunks):
            (directory / name).write_bytes(chunk)
            parts.append({
                "filename": name, "bytes": len(chunk),
                "sha256": hashlib.sha256(chunk).hexdigest(),
            })
        return content, {
            "filename": "resource.tar.gz", "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(), "parts": parts,
        }

    def test_multipart_order_and_corruption_preserve_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content, item = self.multipart_fixture(root)
            output = root / "cache/resource.tar.gz"
            result = INSTALLER.assemble_parts(root, item, output)
            self.assertEqual(result.read_bytes(), content)
            output.write_bytes(b"previous download")
            (root / item["parts"][0]["filename"]).write_bytes(b"broken part")
            with self.assertRaises(ValueError):
                INSTALLER.assemble_parts(root, item, output)
            self.assertEqual(output.read_bytes(), b"previous download")

    def test_multipart_download_reuses_verified_parts_after_interruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content, item = self.multipart_fixture(root)
            cache = root / "cache"
            config = {"release_tag": "fixture", "repository": "fixture/fixture"}
            fetched = []

            def fake_download(command, check):
                self.assertTrue(check)
                name = command[command.index("--pattern") + 1]
                folder = Path(command[command.index("--dir") + 1])
                (folder / name).write_bytes((root / name).read_bytes())
                fetched.append(name)

            with patch.object(INSTALLER.urllib.request, "urlopen", side_effect=OSError("offline")), \
                 patch.object(INSTALLER.shutil, "which", return_value="gh"), \
                 patch.object(INSTALLER.subprocess, "run", side_effect=fake_download):
                archive = INSTALLER.download_archive(cache, item, config, workers=2)
                self.assertEqual(archive.read_bytes(), content)
                self.assertEqual(len(fetched), 2)
                archive.unlink()
                missing = item["parts"][1]["filename"]
                (cache / missing).unlink()
                restored = INSTALLER.download_archive(cache, item, config, workers=2)
                self.assertEqual(restored.read_bytes(), content)
                self.assertEqual(fetched.count(missing), 2)
                self.assertEqual(len(fetched), 3)
                INSTALLER.download_archive(cache, item, config, workers=2)
                self.assertEqual(len(fetched), 3)

    def test_public_resource_does_not_require_github_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = b"author constructed scene fixture"
            item = {"filename": "scenes.tar.gz", "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "release_tag": "scenes-version"}
            config = {"repository": "fixture/fixture", "release_tag": "old"}
            with patch.object(INSTALLER.urllib.request, "urlopen", return_value=io.BytesIO(payload)) as request, \
                 patch.object(INSTALLER.subprocess, "run") as gh:
                archive = INSTALLER.download_archive(Path(directory), item, config)
            self.assertEqual(archive.read_bytes(), payload)
            self.assertIn("/scenes-version/scenes.tar.gz", request.call_args.args[0])
            gh.assert_not_called()

    def test_verified_install_is_idempotent_and_rejects_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "resource.tar.gz"
            name = "assets/example/data.txt"
            content = b"fixed resource example"
            with tarfile.open(archive, "w:gz") as bundle:
                entry = tarfile.TarInfo(name)
                entry.size = len(content)
                bundle.addfile(entry, io.BytesIO(content))
            manifest = {"files": [{
                "path": name, "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }]}
            (root / "manifest.json").write_text(json.dumps(manifest))
            item = {
                "manifest": "manifest.json", "bytes": archive.stat().st_size,
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            }
            previous = INSTALLER.ROOT
            INSTALLER.ROOT = root
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    INSTALLER.install(archive, item, False)
                    INSTALLER.install(archive, item, False)
                self.assertEqual((root / name).read_bytes(), content)
                (root / name).write_bytes(b"local edit")
                with self.assertRaises(ValueError):
                    INSTALLER.install(archive, item, False)
                self.assertEqual((root / name).read_bytes(), b"local edit")
            finally:
                INSTALLER.ROOT = previous
