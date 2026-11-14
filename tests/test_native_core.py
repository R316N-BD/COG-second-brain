import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cog_core import cli

class NativeCoreTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)

    def test_init_preserves_configuration(self):
        target = self.temp / "private data"
        cli.init_vault(target)
        config = target / "config/cog.json"
        original = json.loads(config.read_text(encoding="utf-8"))
        self.assertFalse(original["hermes"]["enabled"])
        config.write_text("custom", encoding="utf-8")
        cli.init_vault(target)
        self.assertEqual(config.read_text(encoding="utf-8"), "custom")
        self.assertTrue((target / "vault/05-knowledge").is_dir())

    def test_rejects_repository_data(self):
        with self.assertRaises(ValueError):
            cli.init_vault(cli.ROOT / "private")
        repo = self.temp / "repo"
        (repo / ".git").mkdir(parents=True)
        with self.assertRaises(ValueError):
            cli.init_vault(repo / "private")

    def test_validation_shipped_framework(self):
        result = cli.validate()
        self.assertTrue(result["ok"], result["errors"])
        self.assertGreater(result["skills"], 0)

    def test_validation_detects_drift(self):
        fixture = self.temp / "framework"
        for item in (".claude-plugin", ".claude/skills", "skills"):
            shutil.copytree(cli.ROOT / item, fixture / item)
        for item in ("plugin.json", "marketplace-entry.json", "COG-VERSION",
                     "AGENTS.md", "README.md", "SETUP.md", "CONTRIBUTING.md",
                     ".github/MARKETPLACE.md", "docs/AGENT-SUPPORT.md"):
            dest = fixture / item
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cli.ROOT / item, dest)
        (fixture / "skills/onboarding/SKILL.md").write_text("drift", encoding="utf-8")
        self.assertIn("Skill mirror differs from canonical skills.", cli.validate(fixture)["errors"])

    def test_doctor_does_not_initialize(self):
        target = self.temp / "not created"
        result = cli.doctor(target)
        self.assertFalse(result["vault_initialized"])
        self.assertFalse(target.exists())

    def test_preview_offline_only_reads(self):
        with patch.object(cli, "git", side_effect=["a" * 40, "b" * 40]) as git:
            result = cli.update_preview(offline=True)
        self.assertIsNone(result["remote_upstream_head"])
        self.assertEqual(git.call_count, 2)
        self.assertTrue(all(call.args[1] == "rev-parse" for call in git.call_args_list))

    def test_cli_initializes_path_with_spaces(self):
        target = self.temp / "data with spaces"
        result = subprocess.run([sys.executable, "-m", "cog_core", "--data-dir",
                                 str(target), "init"], cwd=cli.ROOT,
                                capture_output=True, text=True, check=True)
        self.assertTrue(json.loads(result.stdout)["initialized"])
