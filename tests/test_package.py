import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build import outputs
from scripts.verify import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_generated_files_and_manifest_match_sources(self):
        for path, expected in outputs(ROOT).items():
            self.assertEqual((ROOT / path).read_bytes(), expected, path)
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(verify_manifest(ROOT, manifest), [])

    def test_missing_corrupt_and_escaping_artifacts_fail_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "example.txt"
            path.write_bytes(b"approved\n")
            record = {"url": path.name, "bytes": 9,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            manifest = {"schema_version": 1, "package": "technocore-sonnet",
                        "files": {path.name: record}}
            self.assertEqual(verify_manifest(root, manifest), [])
            path.write_bytes(b"tampered\n")
            self.assertIn("mismatch", verify_manifest(root, manifest)[0])
            path.unlink()
            self.assertIn("missing", verify_manifest(root, manifest)[0])
            manifest["files"] = {"../outside": {**record, "url": "../outside"}}
            with self.assertRaisesRegex(ValueError, "unsafe"):
                verify_manifest(root, manifest)
            manifest["files"] = {}
            with self.assertRaisesRegex(ValueError, "nonempty"):
                verify_manifest(root, manifest)

    def test_commands_succeed_and_invalid_word_exits_nonzero(self):
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        zero_syllable_did = "did:key:z6MkowHQwsx9xr84WbWN3YCnKutyBnBXkT1ChKY4uEAAMzte"
        commands = [
            ["scripts/build.py", "--check"],
            ["scripts/verify.py"],
            ["sonnet_validate.py", "cmudict.dict", "examples/format-poem.txt", "--exact-ten"],
            ["scripts/check_word.py", did, "The"],
        ]
        for args in commands:
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "scripts/check_word.py", did, "wool"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("letters absent", result.stderr)

        result = subprocess.run(
        [sys.executable, "scripts/check_word.py", zero_syllable_did, "Shh,"],
              cwd=ROOT, capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("word: 'shh' has no vowel phone in the frozen dictionary", result.stderr)
        self.assertNotIn("word: word:", result.stderr)


if __name__ == "__main__":
    unittest.main()
