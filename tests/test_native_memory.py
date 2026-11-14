from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cog_core import cli, memory, integrations

class MemoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = cli.init_vault(Path(temp.name) / "data")
        self.vault = self.data / "vault"

    def note(self, path, text):
        target = self.vault / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_index_and_recall(self):
        self.note("04-projects/hermes.md", "# Hermes setup\nWindows gateway configuration.")
        self.note("02-personal/other.md", "# Other\nWindows gateway.")
        result = memory.rebuild(self.data)
        self.assertEqual(result["indexed"], 2)
        rows = memory.search(self.data, "Windows gateway", scope="04-projects")["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["path"], "04-projects/hermes.md")
        self.assertEqual(len(rows[0]["sha256"]), 64)

    def test_rebuild_removes_deleted_notes(self):
        note = self.note("05-knowledge/note.md", "uniqueword")
        memory.rebuild(self.data)
        note.unlink()
        memory.rebuild(self.data)
        self.assertEqual(memory.search(self.data, "uniqueword")["results"], [])

    def test_search_does_not_create_database(self):
        with self.assertRaises(ValueError):
            memory.search(self.data, "test")
        self.assertFalse((self.data / "memory/search.sqlite3").exists())

    def test_literal_queries_and_limits(self):
        self.note("00-inbox/note.md", "alpha OR beta")
        memory.rebuild(self.data)
        self.assertEqual(len(memory.search(self.data, 'alpha OR beta "')["results"]), 1)
        for query in ("", "***"):
            with self.assertRaises(ValueError):
                memory.search(self.data, query)
        with self.assertRaises(ValueError):
            memory.search(self.data, "alpha", limit=100)
        with self.assertRaises(ValueError):
            memory.search(self.data, "alpha", scope="../")

    def test_hidden_and_binary_excluded(self):
        self.note(".hidden/secret.md", "privateword")
        self.note("00-inbox/plain.txt", "privateword")
        (self.vault / "00-inbox/binary.md").write_bytes(b"\xff\xff")
        result = memory.rebuild(self.data)
        self.assertEqual(result["indexed"], 0)
        self.assertEqual(len(result["skipped"]), 1)

    def test_skip_symlinks(self):
        outside = self.data / "external.md"
        outside.write_text("outsideword", encoding="utf-8")
        try:
            (self.vault / "00-inbox/link.md").symlink_to(outside)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        self.assertEqual(memory.rebuild(self.data)["indexed"], 0)

    def test_integration_discovery_not_connection(self):
        with patch.object(integrations.shutil, "which", return_value="/example/tool"):
            result = integrations.discover()
        self.assertTrue(any(x["status"] == "detected" for x in result["integrations"]))
        self.assertTrue(all(not x["connected"] for x in result["integrations"]))
