from pathlib import Path
import tempfile
import unittest
from cog_core import cli, memory

class IncrementalTests(unittest.TestCase):
    def test_update_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = cli.init_vault(Path(tmp) / "data")
            a = root / "vault/04-projects/a.md"
            b = root / "vault/04-projects/b.md"
            a.write_text("unchanged", encoding="utf-8")
            b.write_text("old", encoding="utf-8")
            memory.rebuild(root)
            b.write_text("newword", encoding="utf-8")
            result = memory.rebuild(root, incremental=True)
            self.assertEqual((result["indexed"], result["unchanged"]), (1,1))
            self.assertEqual(len(memory.search(root, "newword")["results"]), 1)
            self.assertFalse(memory.search(root, "old")["results"])
            b.unlink()
            self.assertEqual(memory.rebuild(root, incremental=True)["removed"], 1)
