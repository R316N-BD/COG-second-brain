from pathlib import Path
import tempfile
import unittest
from cog_core import cli, backup

class BackupTests(unittest.TestCase):
    def test_round_trip_and_wrong_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = cli.init_vault(Path(tmp) / "data")
            note = root / "vault/05-knowledge/sample.md"
            note.write_text("private sample", encoding="utf-8")
            password = "test-passphrase-only"
            result = backup.create(root, password)
            archive = Path(result["backup"])
            self.assertNotIn(b"private sample", archive.read_bytes())
            destination = Path(tmp) / "restored"
            with self.assertRaises(ValueError):
                backup.restore(archive, destination, "incorrect-password")
            self.assertFalse(destination.exists())
            restored = backup.restore(archive, destination, password)
            self.assertEqual(restored["restored"], 1)
            self.assertEqual((destination / "vault/05-knowledge/sample.md").read_text(encoding="utf-8"), "private sample")
            with self.assertRaises(ValueError):
                backup.restore(archive, destination, password)
