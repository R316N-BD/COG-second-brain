from pathlib import Path
import tempfile
import unittest
from cog_core import cli, memory, operations, policy
from cog_core.gateway import Gateway

class GatewayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = cli.init_vault(Path(temp.name) / "data")
        self.public = self.data / "vault/05-knowledge/example.md"
        self.public.write_text("# Example\nshared keyword", encoding="utf-8")
        self.private = self.data / "vault/02-personal/secret.md"
        self.private.write_text("shared keyword", encoding="utf-8")
        memory.rebuild(self.data)
        self.gateway = Gateway(self.data, "hermes-research")

    def test_scope_is_enforced(self):
        result = self.gateway.search("shared", "05-knowledge")
        self.assertEqual(len(result["results"]), 1)
        for scope in ("02-personal", "", None):
            with self.assertRaises(PermissionError):
                self.gateway.search("shared", scope)
        with self.assertRaises(PermissionError):
            self.gateway.read("02-personal/secret.md")

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            self.gateway.read("05-knowledge/../02-personal/secret.md")

    def test_stale_search_suppressed(self):
        self.public.unlink()
        self.assertEqual(self.gateway.search("shared", "05-knowledge")["results"], [])

    def test_proposal_approval_is_not_execution(self):
        result = self.gateway.propose("05-knowledge/new.md", "# New")
        with self.assertRaises(ValueError):
            operations.decide(self.data, result["id"], "wrong", True)
        operations.decide(self.data, result["id"], result["sha256"], True)
        self.assertFalse((self.data / "vault/05-knowledge/new.md").exists())
        with self.assertRaises(ValueError):
            operations.decide(self.data, result["id"], result["sha256"], True)

    def test_jobs_state_machine(self):
        job = operations.create_job(self.data, "Review", "hermes-research")
        with self.assertRaises(ValueError):
            operations.job_transition(self.data, job["id"], "completed")
        operations.job_transition(self.data, job["id"], "running")
        operations.job_transition(self.data, job["id"], "completed")
        self.assertEqual(operations.list_jobs(self.data)[0]["status"], "completed")
        self.assertGreaterEqual(len(operations.audit_events(self.data)), 3)

    def test_revoked_profile_is_denied(self):
        path = self.data / "config/agents.json"
        path.write_text('{"schema_version":1,"profiles":{}}', encoding="utf-8")
        with self.assertRaises(PermissionError):
            self.gateway.read("05-knowledge/example.md")
