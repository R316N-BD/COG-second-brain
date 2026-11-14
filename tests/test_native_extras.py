from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cog_core import cli, graph, operations, maintenance, adapters
from cog_core.gateway import Gateway

class ExtraTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = cli.init_vault(Path(tmp.name) / "data")

    def test_approved_create_only(self):
        g = Gateway(self.root, "hermes-research")
        proposal = g.propose("05-knowledge/new.md", "approved")
        ident, digest = proposal["id"], proposal["sha256"]
        with self.assertRaises(ValueError):
            operations.apply_proposal(self.root, ident, digest)
        operations.decide(self.root, ident, digest, True)
        operations.apply_proposal(self.root, ident, digest)
        note = self.root / "vault/05-knowledge/new.md"
        self.assertEqual(note.read_text(encoding="utf-8"), "approved")
        with self.assertRaises(ValueError):
            operations.apply_proposal(self.root, ident, digest)
        p2 = g.propose("05-knowledge/new.md", "overwrite")
        operations.decide(self.root, p2["id"], p2["sha256"], True)
        with self.assertRaises(FileExistsError):
            operations.apply_proposal(self.root, p2["id"], p2["sha256"])
        self.assertEqual(note.read_text(encoding="utf-8"), "approved")

    def test_graph(self):
        (self.root / "vault/05-knowledge/a.md").write_text("[[b]] [[missing]]", encoding="utf-8")
        (self.root / "vault/05-knowledge/b.md").write_text("target", encoding="utf-8")
        result = graph.build(self.root)
        self.assertEqual(result["edges"], [{"from": "05-knowledge/a.md", "to": "05-knowledge/b.md"}])
        self.assertEqual(result["unresolved"][0]["reason"], "missing")

    def test_maintenance(self):
        result = maintenance.run(self.root, "index-refresh")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(operations.list_jobs(self.root)[0]["status"], "completed")
        with self.assertRaises(ValueError):
            maintenance.run(self.root, "shell")

    def test_github_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            adapters.github_status("--bad/repo")
        with patch.object(adapters.shutil, "which", return_value=None):
            with self.assertRaises(ValueError):
                adapters.github_status("owner/repo")
