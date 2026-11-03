import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.setup_voice_model import MODEL_NAME, install_model, model_is_complete


class SetupVoiceModelTests(unittest.TestCase):
    def make_archive(self, path: Path, malicious: bool = False) -> None:
        with zipfile.ZipFile(path, "w") as zf:
            for member in ("am/final.mdl", "conf/model.conf", "graph/HCLr.fst", "graph/Gr.fst"):
                zf.writestr(f"{MODEL_NAME}/{member}", "fixture")
            if malicious:
                zf.writestr(f"{MODEL_NAME}/../escaped.txt", "unsafe")

    def test_installs_and_checks_local_archive_without_microphone(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "model.zip"
            self.make_archive(archive)
            target = root / "models" / MODEL_NAME
            installed, digest = install_model(target, url=archive.as_uri())
            self.assertEqual(installed, target)
            self.assertEqual(len(digest), 64)
            self.assertTrue(model_is_complete(target))
            self.assertEqual(install_model(target), (target, None))

    def test_rejects_path_traversal_without_publishing_partial_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "malicious.zip"
            self.make_archive(archive, malicious=True)
            target = root / "models" / MODEL_NAME
            with self.assertRaises(ValueError):
                install_model(target, url=archive.as_uri())
            self.assertFalse(target.exists())
            self.assertFalse((root / "escaped.txt").exists())

    def test_rejects_wrong_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "model.zip"
            self.make_archive(archive)
            target = root / "models" / MODEL_NAME
            with self.assertRaisesRegex(ValueError, "SHA-256 no coincide"):
                install_model(target, url=archive.as_uri(), expected_sha256="0" * 64)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
